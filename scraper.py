
import os
import sys

from helpers.format import to_snake_case
from helpers.log import get_logger
from schemas import (
    Accumulated,
    BetweenPhases,
    CollectedData,
    EngineData,
    GeneratorData,
    MainsData,
    ModuleState,
    PerPhase,
    PhasePower,
    PhaseValues,
    PowerData,
)

logger = get_logger("scraper")

class SessionController:
    state_file_path = "browsers/state.json"

    def __init__(self, pw):
        self.pw = pw
        #self.let_pass = True

    async def launch_browser(self):
        self.browser = await self.pw.chromium.launch(headless=True)
        return self.browser

    async def run(self):
        await self.launch_browser()
        logger.debug("Browser launched")
        
        try:
            page = await self.inject_state(self.browser)
        except FileNotFoundError:
            page = await self.create_state(self.browser)
            logger.debug("State file created")
                
        except Exception as e:
            logger.debug(e)
            sys.exit(1)
            
        await self.wait_load(page)
        await self.block_background_updates(page)

        self.scraper = Scraper(page)
        data = await self.scraper.get_data()
        
        return data

    async def stop(self):
        await self.browser.close()
        logger.info("Goodbye...")

    async def wait_load(self, page):

        all_off = True
        
        async def check_leds_off(page):
            leds = ["LED_8", "LED_9", "LED_11"]
            results = {}

            for led_id in leds:
                selector = f"#{led_id}"
                led_element = await page.query_selector(selector)

                if led_element is None:
                    results[led_id] = "not found"
                    continue

                class_attr = await led_element.get_attribute("class")
                results[led_id] = "off" if "LEDOff" in class_attr else "on"

            # Todos estão off?
            all_off = all(state == "off" for state in results.values())

            return all_off

        while all_off:
            all_off = await check_leds_off(page)

        logger.debug("Page loaded")
        self.let_pass = False

    async def inject_state(self, browser):

        try:

            if os.path.isfile(self.state_file_path):
                logger.debug("State file located")
            else:
                raise FileNotFoundError
            
            context = await browser.new_context()
            await context.close()
            new_context = await browser.new_context(storage_state=self.state_file_path)
            page = await new_context.new_page()
            
            await page.goto(f"{os.getenv("DSE_URL")}/secure/index.html")

            if await self.validate_login(page):
                logger.debug("Injected context with success")
                return page
            else:
                #delete state file
                os.remove(self.state_file_path)
                raise FileNotFoundError

        except Exception:
            raise FileNotFoundError
            
    async def validate_login(self, page) -> bool:
        try:
            await page.wait_for_selector("#logindetail")
            return True
        except Exception as e:
            logger.exception(e)
            return False
            
    async def create_state(self, browser):
        logger.debug("Creating state")
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(os.getenv("DSE_URL"))
        await self.sign_in(page)
        if await self.validate_login(page):
            #save state 
            await page.context.storage_state(path=self.state_file_path)
            logger.debug("Context created with success")
            
            return page
        
    async def sign_in(self, page):
        
        await page.fill("#username", os.getenv("DSE_USER"))
        await page.fill("#password", os.getenv("DSE_PASSWORD"))
        await page.click("#login")

        return
    
    async def block_background_updates(self, page):

        #pass 1 request
        #self.let_pass = True
        
        async def handle_route(route, request):
            url = request.url
            resource = request.resource_type
            if resource in ["xhr"] and "/realtime.cgi" in url:
                if self.let_pass:
                    logger.debug(f"✅ Liberando {resource} → {url} ({self.let_pass} restantes)")
                    await route.continue_()
                    return
                logger.warning(f"⛔ Bloqueando {resource} → {url}")
                await route.abort()
            else:
                await route.continue_()


        await page.route("**/*", handle_route)

class Scraper:

    def __init__(self, page):
        self.page = page

    async def get_data(self):

        start_state_data = await self.get_start_state()
        module_state_data = await self.get_module_state()

        scada_div = await self.page.query_selector("div#SCADA")

        tables = await scada_div.query_selector_all(":scope > table")

        for table in tables:
            first_row = await table.query_selector("tr")
            first_td = await first_row.query_selector("td")
            text = (await first_td.inner_text()).strip().lower()

            if text == "generator":
               generator_data = await self.get_generator_data(table)

            if text == "mains":
                mains_data = await self.get_mains_data(table)

            if text == "power":
                power_data = await self.get_power_data(table)

            if text == "engine":
                engine_data = await self.get_engine_data(table)
            
        data = CollectedData(
            start_state=start_state_data,
            module_state=module_state_data,
            generator=generator_data,
            mains=mains_data,
            power=power_data,
            engine=engine_data
        )

        return data

    async def get_start_state(self):
        leds = {
            "LED_8":"off",
            "LED_9": "on",
            "LED_11": "auto"
        }

        for led_id, led_name in leds.items():
            selector = f"#{led_id}"
            led_element = await self.page.query_selector(selector)

            if led_element is None:
                exception = Exception(f"Led {led_id} not found")
                logger.error(exception)
                raise exception

            class_attr = await led_element.get_attribute("class")
            is_on = "LEDOff" not in class_attr
            if is_on:
                return led_name
            
    async def get_module_state(self):

        async def get_accumulated(page):
            # Primeiro, encontra o bloco A
            block = await page.query_selector("#blockA .infotable")

            if block is None:
                raise Exception("BlockA infotable not found")

            # Define os rótulos que você quer buscar
            keys = {
                "kwh": 0.0,
                "kvah": 0.0,
                "kvarh": 0.0
            }

            # Encontra todas as linhas (tr) da tabela
            rows = await block.query_selector_all("tr")

            for row in rows:
                label_cell = await row.query_selector("td.lable")
                if not label_cell:
                    continue

                label_text = (await label_cell.inner_text()).strip()

                if label_text in keys:
                    value_cell = await row.query_selector("td:nth-child(2) .cellValue")
                    if value_cell:
                        value_text = await value_cell.inner_text()
                        try:
                            keys[label_text] = float(value_text)
                        except ValueError:
                            keys[label_text] = 0.0  # ou 0.0, se preferir default

            return keys

        await self.page.wait_for_selector("div#moduleState .infotable")

        rows = await self.page.query_selector_all("div#moduleState .infotable tr")

        data = {}

        for i in range(0, len(rows), 2):
            title_row = rows[i]
            value_row = rows[i+1]

            title = (await title_row.inner_text()).strip()
            sneak_title = to_snake_case(title)
            
            cell_div = await value_row.query_selector(".cellValue")
            value = (await cell_div.inner_text()).strip()
            sneak_value = to_snake_case(value)
            
            data[sneak_title] = sneak_value

        accumulated = await get_accumulated(self.page)

        data["accumulated"] = Accumulated(**accumulated)

        return ModuleState(**data)

    async def get_generator_data(self, table):
        sub_tables = await table.query_selector_all("table")
        left_table, right_table = sub_tables
        async def left_table_data(): #between phases
            result = {}
            for row in await left_table.query_selector_all("tr"):
                text = (await row.inner_text()).strip()

                parts = text.split()
                if not parts:
                    continue

                # Detectar linha de tensão
                if parts[0] == "V" and len(parts) >= 4:
                    result["l1_l2"] = float(parts[1])
                    result["l2_l3"] = float(parts[2])
                    result["l3_l1"] = float(parts[3])

                # Detectar linha de frequência
                elif parts[0].lower().startswith("frequency") and len(parts) >= 2:
                    result["freq"] = float(parts[1])

            return BetweenPhases(**result)
        between_phases = await left_table_data()

        async def right_table_data(): #per phase
            rows = await right_table.query_selector_all("tr")
            
            voltages = {}
            currents = {}

            for row in rows:
                text = (await row.inner_text()).strip()

                parts = text.split()
                if not parts:
                    continue

                if parts[0] == "V" and len(parts) >= 4:
                    voltages = {
                        "l1": float(parts[1]),
                        "l2": float(parts[2]),
                        "l3": float(parts[3]),
                    }
                elif parts[0] == "A" and len(parts) >= 4:
                    currents = {
                        "l1": float(parts[1]),
                        "l2": float(parts[2]),
                        "l3": float(parts[3]),
                    }

            return PerPhase(
                l1=PhaseValues(v=voltages["l1"], a=currents["l1"]),
                l2=PhaseValues(v=voltages["l2"], a=currents["l2"]),
                l3=PhaseValues(v=voltages["l3"], a=currents["l3"]),
            )
        per_phase = await right_table_data()

        return GeneratorData(
            between_phases=between_phases,
            per_phase=per_phase
        )

    async def get_mains_data(self, table):
        sub_tables = await table.query_selector_all("table")
        left_table, right_table = sub_tables
        
        async def left_table_data(): #between phases
            result = {}
            for row in await left_table.query_selector_all("tr"):
                text = (await row.inner_text()).strip()

                parts = text.split()
                if not parts:
                    continue

                # Detectar linha de tensão
                if parts[0].lower() == "v":
                    result["l1_l2"] = float(parts[1])
                    result["l2_l3"] = float(parts[2])
                    result["l3_l1"] = float(parts[3])

                # Detectar linha de frequência
                elif parts[0].lower().startswith("frequency") and len(parts) >= 2:
                    result["freq"] = float(parts[1])

            return BetweenPhases(**result)
        between_phases = await left_table_data()

        async def right_table_data(): #per phase
            rows = await right_table.query_selector_all("tr")
            
            voltages = {}
            currents = {}

            for row in rows:
                text = (await row.inner_text()).strip()

                parts = text.split()
                if not parts:
                    continue

                if parts[0] == "V" and len(parts) >= 4:
                    voltages = {
                        "l1": float(parts[1]),
                        "l2": float(parts[2]),
                        "l3": float(parts[3]),
                    }
                elif parts[0] == "A" and len(parts) >= 4:
                    currents = {
                        "l1": float(parts[1]) if parts[1] != "#" else 0.0,
                        "l2": float(parts[2]) if parts[1] != "#" else 0.0,
                        "l3": float(parts[3]) if parts[1] != "#" else 0.0,
                    }

            return PerPhase(
                l1=PhaseValues(v=voltages["l1"], a=currents["l1"]),
                l2=PhaseValues(v=voltages["l2"], a=currents["l2"]),
                l3=PhaseValues(v=voltages["l3"], a=currents["l3"]),
            )
        per_phase = await right_table_data()

        return MainsData(
            between_phases=between_phases,
            per_phase=per_phase
        )

    async def get_power_data(self, table):
        sub_table = await table.query_selector_all("table")
        sub_table = sub_table[0]
        kw_values = []
        kva_values = []
        kvar_values = []
        pf_values = []


        rows = await sub_table.query_selector_all("tr")
        for row in rows:
            text = (await row.inner_text()).strip()
            parts = text.split()

            if not parts:
                continue

            key = parts[0].lower()
            values = parts[1:]

            if key == "kw":
                kw_values = [float(v) if v != "-" else 0.0 for v in values]
            elif key == "kva":
                kva_values = [float(v) if v != "-" else 0.0 for v in values]
            elif key == "kvar":
                kvar_values = [float(v) if v != "-" else 0.0 for v in values]
            elif key == "pf":
                pf_values = [float(v) if v != "-" else 0.0 for v in values]

        def build_phase(i: int):
            return PhasePower(
                kw=kw_values[i],
                kva=kva_values[i],
                kvar=kvar_values[i],
                pf=pf_values[i],
            )

        return PowerData(
            l1=build_phase(0),
            l2=build_phase(1),
            l3=build_phase(2),
            total=build_phase(3),
        )

    async def get_engine_data(self, table) -> EngineData:
        sub_tables = await table.query_selector_all("table")
        sub_table = sub_tables[0]
        rows = await sub_table.query_selector_all("tr")

        data = {
            "speed": 0.0,
            "oil_pressure": 0.0,
            "coolant_temperature": 0.0,
            "fuel_level": 0,
            "charge_alternator": 0.0,
            "engine_battery": 0.0,
            "engine_starts": 0,
            "engine_minutes": 0
        }

        for row in rows:
            text = (await row.inner_text()).strip()
            parts = text.split()

            if parts[:2] == ["Engine", "Speed"]:
                data["speed"] = float(parts[2].replace("RPM", "").replace("#", "") or 0)

            elif parts[:2] == ["Oil", "Pressure"]:
                data["oil_pressure"] = float(parts[2].replace("KPa", "").replace("#", "") or 0)

            elif parts[:2] == ["Coolant", "Temperature"]:
                data["coolant_temperature"] = float(parts[2].replace("°C", "").replace("#", "") or 0)

            elif parts[:2] == ["Fuel", "Level"]:
                data["fuel_level"] = int(parts[2].replace("%", "").replace("#", "") or 0)

            elif parts[:2] == ["Charge", "Alternator"]:
                data["charge_alternator"] = float(parts[2].replace("V", "").replace("#", "") or 0)

            elif parts[:2] == ["Engine", "Battery"]:
                data["engine_battery"] = float(parts[2].replace("V", "").replace("#", "") or 0)

            elif parts[:2] == ["Engine", "Starts"]:
                data["engine_starts"] = int(parts[2].replace("starts", "").replace("#", "") or 0)

            elif parts[:2] == ["Engine", "Hours"]:
                hours = int(parts[2].replace("h", "").replace("#", "") or 0)
                minutes = int(parts[3].replace("m", "").replace("#", "") or 0)
                data["engine_minutes"] = hours * 60 + minutes

        return EngineData(**data)