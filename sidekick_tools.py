from playwright.async_api import async_playwright
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from dotenv import load_dotenv
import os
import requests
from langchain.agents import Tool
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from twilio.rest import Client as TwilioClient
from amadeus import Client as AmadeusClient
from langchain_tavily import TavilySearch
load_dotenv(override=True)


# Configure Amadeus Client for flight and hotel search
# We'll only initialize it if keys are provided, inside the tool later
amadeus_api_key = os.environ["AMADEUS_CLIENT_ID"]
amadeus_api_secret = os.environ["AMADEUS_CLIENT_SECRET"]
amadeus_client = AmadeusClient(
    client_id = amadeus_api_key,
    client_secret = amadeus_api_secret,
    hostname = "test",  # Start with the test environment
)
tavily_api_key = os.environ["TAVILY_API_KEY"]
#tavily_search_tool = TavilySearchResults(max_results = 3)
tavily_search_tool = TavilySearch(k=3)
# List of tools for this step
tools_list_single = [tavily_search_tool]


#pushover_token = os.getenv("PUSHOVER_TOKEN")
#pushover_user = os.getenv("PUSHOVER_USER")
#pushover_url = "https://api.pushover.net/1/messages.json"
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
my_whatsapp_number = os.getenv("MY_WHATSAPP_NUMBER")
client = TwilioClient(account_sid, auth_token)
serper = GoogleSerperAPIWrapper()

async def playwright_tools():
    playwright = await async_playwright().start()
    #browser = await playwright.chromium.launch(headless=False)
    try:
        browser = await playwright.chromium.launch(headless=False)
    except Exception as e:
        print("Playwright browser not found, trying to auto-install...")
        import subprocess, sys
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        browser = await playwright.chromium.launch(headless=False)


    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    return toolkit.get_tools(), browser, playwright
##############
# go to this link to set up Twilio WhatsApp sandbox: https://www.twilio.com/docs/whatsapp/sandbox , https://www.twilio.com/console/sms/whatsapp/learn
#############
def send_whatsapp(text: str):
    """Send a WhatsApp message via Twilio"""
    message = client.messages.create(
        from_=twilio_whatsapp_number,
        to=my_whatsapp_number,
        body=text  # simple text message (no need for content_sid)
    )
#def push(text: str):
#    """Send a push notification to the user"""
#    requests.post(pushover_url, data = {"token": pushover_token, "user": pushover_user, "message": text})
#    return "success"


def get_file_tools():
    toolkit = FileManagementToolkit(root_dir="sandbox")
    return toolkit.get_tools()





#################Travel Agent Tools ####################

def search_hotels_tool(city_code: str, check_in_date: str, check_out_date: str, adults: int = 1):
    """
    Searches for available hotel options in a specific city for given dates using Amadeus.
    Requires the IATA city code (e.g., 'PAR', 'BER') and dates in 'YYYY-MM-DD' format. Use get_current_date_tool first if dates are relative.
    """

    print(
        f"DEBUG: Calling Amadeus Hotel Search - City: {city_code}, Check-in: {check_in_date}, Check-out: {check_out_date}, Adults: {adults}"
    )
    # Call Amadeus API - Hotel Search (find hotels by city)
    hotel_list_response = amadeus_client.reference_data.locations.hotels.by_city.get(
        cityCode=city_code, radius=50, radiusUnit="KM"
    )

    if not hotel_list_response.data or len(hotel_list_response.data) == 0:
        return f"No hotels found listed in Amadeus for city code {city_code}."

    # Get hotel IDs from the response (limit to first 5 for offers search)
    hotel_ids = [hotel["hotelId"] for hotel in hotel_list_response.data[:5]]

    # Now search for offers for these specific hotels
    hotel_offer_response = amadeus_client.shopping.hotel_offers_search.get(
        hotelIds=",".join(hotel_ids),
        checkInDate=check_in_date,
        checkOutDate=check_out_date,
        adults=adults, # we need to pass the number of adults
        bestRateOnly=True,  # Try to get simpler results
    )

    # Process the response (simplified)
    if hotel_offer_response.data and len(hotel_offer_response.data) > 0:
        results = []
        for offer in hotel_offer_response.data[:5]:  # Limit to showing 3 offers
            hotel_name = offer.get("hotel", {}).get("name", "N/A")
            price = offer.get("offers", [{}])[0].get("price", {}).get("total", "N/A")
            currency = offer.get("offers", [{}])[0].get("price", {}).get("currency", "")
            results.append(f"Hotel: {hotel_name}, Price: {price} {currency} (approx)")
        return "Found hotel options:\n- " + "\n- ".join(results)
    else:
        return f"No available hotel offers found for the dates in {city_code} among the checked hotels."


def search_flights_tool(
    origin_code: str,
    destination_code: str,
    departure_date: str,
    return_date: str | None = None,
    adults: int = 1,
    travel_class: str = "ECONOMY",
    currency: str = "USD",
    max_offers: int = 5,
):
    """
    Searches live flight prices and availability via Amadeus Flight Offers Search API.
    Required:
        origin_code, destination_code – IATA airport/city codes (e.g., 'YYZ', 'LHR')
        departure_date – 'YYYY-MM-DD'
    Optional:
        return_date – for round‑trips; omit for one‑way
        adults – number of adult passengers (default 1)
        travel_class – 'ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'
        currency – 3‑letter code for pricing (default USD)
        max_offers – how many offers to list back
    """

    print(
        f"DEBUG: Calling Amadeus Flight Search – "
        f"{origin_code}->{destination_code}, "
        f"Depart {departure_date}, Return {return_date}, "
        f"Adults {adults}, Class {travel_class}"
    )

    # --- Call Amadeus Flight Offers Search API ---
    flight_search_params = {
        "originLocationCode": origin_code,
        "destinationLocationCode": destination_code,
        "departureDate": departure_date,
        "adults": adults,
        "travelClass": travel_class,
        "currencyCode": currency,
        "max": max_offers,
    }
    if return_date:
        flight_search_params["returnDate"] = return_date

    response = amadeus_client.shopping.flight_offers_search.get(**flight_search_params)

    # --- Parse the response ---
    if not response.data:
        return (
            f"No flight offers found for {origin_code} → {destination_code} on "
            f"{departure_date}{' (return '+return_date+')' if return_date else ''}."
        )

    results = []
    for offer in response.data[:max_offers]:
        price = offer["price"]["total"]
        airline = offer["validatingAirlineCodes"][0]
        itinerary = offer["itineraries"][0]
        segments = itinerary["segments"]
        first_leg = segments[0]
        last_leg = segments[-1]
        dep_time = first_leg["departure"]["at"][:16].replace("T", " ")
        arr_time = last_leg["arrival"]["at"][:16].replace("T", " ")
        duration = itinerary["duration"].replace("PT", "")
        results.append(f"{airline} | {dep_time} → {arr_time} | {duration} | {price} {currency}")

    return "Found flight options:\n- " + "\n- ".join(results)

######################all tools push###########################
async def other_tools():
    #push_tool = Tool(name="send_push_notification", func=push, description="Use this tool when you want to send a push notification")
    push_tool = Tool(
        name="send_push_notification_whatsapp",
        func=send_whatsapp,
        description="useful for when you want to send a push notification"
    )
    file_tools = get_file_tools()

    tool_search =Tool(
        name="search",
        func=serper.run,
        description="Use this tool when you want to get the results of an online web search"
    )
    #flight and hotel helping tools
    tool_search_flights = Tool(
    name="search_flights",
    func=search_flights_tool,
    description=(
        "Search flights from origin to destination. "
        "Arguments:\n"
        "- origin_code: IATA code of departure airport (e.g., 'NYC')\n"
        "- destination_code: IATA code of arrival airport (e.g., 'LON')\n"
        "- departure_date: YYYY-MM-DD\n"
        "- return_date: YYYY-MM-DD or omit for one-way\n"
        "- adults: number of passengers\n"
        "- travel_class: ECONOMY, BUSINESS, FIRST\n"
        "- currency: USD, EUR, etc.\n"
        "- max_offers: max results to return"
        )
    )

    tool_search_hotels = Tool(
        name="search_hotels",
        func=search_hotels_tool,
        description=(
            "Search hotels in a city for given dates. "
            "Arguments:\n"
            "- city_code: IATA city code (e.g., 'PAR')\n"
            "- check_in_date: YYYY-MM-DD\n"
            "- check_out_date: YYYY-MM-DD\n"
            "- adults: number of adults (default 1)"
        )
    )

    wikipedia = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=wikipedia)

    python_repl = PythonREPLTool()
    
    return file_tools + [push_tool, tool_search, python_repl,  wiki_tool,tool_search_flights,tool_search_hotels]
