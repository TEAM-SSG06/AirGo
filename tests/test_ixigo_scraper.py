from airgo.scrapers.ixigo.scraper import FareCandidate, parse_result_payload, price_mismatch, select_least_five


def test_selects_five_fares_per_flight_not_five_overall():
    fares = [
        FareCandidate("A", "A1", "08:00", f"F{i}", float(i)) for i in range(1, 8)
    ] + [FareCandidate("B", "B1", "09:00", "ECONOMY", 99.0)]

    selected = select_least_five(fares)

    assert [(fare.flight_number, fare.listing_price) for fare in selected] == [
        ("A1", 1.0), ("A1", 2.0), ("A1", 3.0), ("A1", 4.0), ("A1", 5.0),
        ("B1", 99.0),
    ]


def test_parser_discards_incomplete_observations_without_inventing_data():
    payload = [
        {"carrier": "6E", "flight_number": "6E-1", "departure_time": "08:00", "fare_class": "Saver", "listing_price": "₹4,200"},
        {"carrier": "6E", "flight_number": "", "departure_time": "09:00", "listing_price": "5000"},
        {"carrier": "AI", "flight_number": "AI-2", "departure_time": "10:00", "listing_price": None},
    ]

    parsed = parse_result_payload(payload)

    assert len(parsed) == 1
    assert parsed[0].listing_price == 4200.0


def test_mismatch_flag_compares_listing_and_confirmed_prices():
    assert price_mismatch(4200.0, 4350.0) is True
    assert price_mismatch(4200.0, 4200.004) is False
    assert price_mismatch(4200.0, None) is None
