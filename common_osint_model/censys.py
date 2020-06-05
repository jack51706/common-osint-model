from common_osint_model.utils import flatten
from DateTime import DateTime
from mmh3 import hash as mmh3_hash

def from_censys_ipv4(raw: dict) -> dict:
    """
    Converts a Censys IPv4 dictionary into the common format
    :param raw: Censys IPv4 dict
    :return: Common format dict
    """
    g = {}
    ports = []
    g.update(censys_ipv4_meta_extraction(raw))
    for protocol in raw["protocols"]:
        (port, protocol) = protocol.split("/")
        ports.append(port)
        g.update(censys_ipv4_service_extraction(raw, port, protocol))
    g.update(dict(ports=ports))
    return g


def from_censys_ipv4_flattened(raw: dict) -> dict:
    """
    Converts a Censys IPv4 dictionary into the common format
    :param raw: Censys IPv4 dict
    :return: Common format dict, flattened
    """
    return flatten(from_censys_ipv4(raw))


def censys_ipv4_meta_extraction(raw: dict) -> dict:
    """
    Extracts metadata from Censys IPv4 dicts
    :param raw: Censys IPv4 dict
    :return: Metadata part of common format dict
    """
    _as = raw["autonomous_system"]
    return {
        "ip": raw["ip"],
        "as": {
            "number": _as["asn"],
            "name": _as["name"],
            "location": _as["country_code"],
            "prefix": _as["routed_prefix"],
        },
    }


def censys_ipv4_service_extraction(raw: dict, port: str, protocol: str) -> dict:
    """
    Todo: Add comment
    :param raw:
    :param port:
    :param protocol:
    :return:
    """
    s = raw[port][protocol]
    service = {
        "timestamp": int(DateTime(raw["updated_at"])),
        "timestamp_readable": DateTime(raw["updated_at"]).ISO8601(),
    }
    keys = s.keys()
    if "banner_decoded" in keys:
        service.update(dict(banner=s["banner_decoded"]))
    if "get" in keys:
        http = censys_ipv4_http_extraction(s["get"])
        service.update({"http": http})
    if "tls" in keys:
        tls = censys_ipv4_tls_extraction(s["tls"])
        service.update({"tls": tls})
    return {port: service}


def censys_ipv4_http_extraction(s: dict) -> dict:
    """
    Todo: Add comment
    :param s:
    :return:
    """
    headers = s.get("headers", {})
    for h in headers.get("unknown", []):
        headers.update({h["key"].lower().replace("-", "_"): h["value"]})
    del headers["unknown"]
    return {
        "headers": headers,
        "content": {
            "html": s["body"],
            "hash": {"shodan": mmh3_hash(s["body"]), "sha256": s["body_sha256"]},
            "favicon": {"shodan": None, "sha256": None},
        },
    }


def censys_ipv4_tls_extraction(s: dict) -> dict:
    cert = s.get("certificate", {}).get("parsed", {})
    subject = cert.get("subject", None) or dict()
    issuer = cert.get("issuer", None) or dict()
    return {
        "certificate": {
            "issuer_dn": cert.get("issuer_dn", None),
            "subject_dn": cert.get("subject_dn", None),
            "issuer": {
                "common_name": issuer.get("common_name", None),
                "country": issuer.get("country", None),
                "locality": issuer.get("locality", None),
                "province": issuer.get("province", None),
                "organization": issuer.get("organization", None),
                "organizational_unit": issuer.get("organizational_unit", None),
                "email_address": issuer.get("email_address", None),
            },
            "subject": {
                "common_name": subject.get("common_name", None),
                "country": subject.get("country", None),
                "locality": subject.get("locality", None),
                "province": subject.get("province", None),
                "organization": subject.get("organization", None),
                "organizational_unit": subject.get("organizational_unit", None),
                "email_address": subject.get("email_address", None),
            },
        }
    }