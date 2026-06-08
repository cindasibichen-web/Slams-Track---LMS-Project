from ipaddress import ip_address
from user_agents import parse
from django.conf import settings
from geoip2.database import Reader


def get_client_ip(request):

    x_forwarded_for = request.META.get(
        'HTTP_X_FORWARDED_FOR'
    )

    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()

    return request.META.get(
        'REMOTE_ADDR',
        '0.0.0.0'
    )



def get_browser(user_agent):

    user_agent = user_agent or ''

    if 'PostmanRuntime' in user_agent:
        return 'Postman'

    try:

        ua = parse(user_agent)

        browser = ua.browser.family or 'Unknown Browser'
        version = ua.browser.version_string

        if version:
            return f'{browser} {version}'

        return browser

    except Exception:

        return 'Unknown Browser'



def get_device(user_agent):

    user_agent = user_agent or ''

    if 'PostmanRuntime' in user_agent:
        return 'Postman'

    try:

        ua = parse(user_agent)

        if ua.is_mobile:
            return 'Mobile'

        if ua.is_tablet:
            return 'Tablet'

        if ua.is_pc:
            return 'Desktop'

        return ua.device.family or 'Desktop'

    except Exception:

        return 'Desktop'



def get_location(ip):

    try:

        if not ip:
            return "Unknown Location"

        parsed_ip = ip_address(ip)

        if parsed_ip.is_loopback:
            return "Local Development"

        if parsed_ip.is_private:
            return "Private Network"

        database_path = (
            settings.GEOIP_PATH /
            "GeoLite2-City.mmdb"
        )

        with Reader(str(database_path)) as reader:

            response = reader.city(ip)

            city = response.city.name
            state = response.subdivisions.most_specific.name
            country = response.country.name

            location_parts = []

            if city:
                location_parts.append(city)

            if state:
                location_parts.append(state)

            if country:
                location_parts.append(country)

            if location_parts:
                return ", ".join(location_parts)

            return "Unknown Location"

    except Exception as e:

        print("GEOIP ERROR =", str(e))

        return "Unknown Location"
