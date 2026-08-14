import pytest

from app.services.tcmb import parse_tcmb_xml

SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<Tarih_Date Tarih="14.08.2026" Date="08/14/2026" Bulten_No="2026/152">
  <Currency CrossOrder="0" Kod="USD" CurrencyCode="USD">
    <Unit>1</Unit>
    <Isim>ABD DOLARI</Isim>
    <CurrencyName>US DOLLAR</CurrencyName>
    <ForexBuying>41.10</ForexBuying>
    <ForexSelling>41.30</ForexSelling>
    <BanknoteBuying>41.05</BanknoteBuying>
    <BanknoteSelling>41.40</BanknoteSelling>
  </Currency>
  <Currency CrossOrder="9" Kod="EUR" CurrencyCode="EUR">
    <Unit>1</Unit>
    <Isim>EURO</Isim>
    <CurrencyName>EURO</CurrencyName>
    <ForexBuying>46.40</ForexBuying>
    <ForexSelling>46.60</ForexSelling>
  </Currency>
  <Currency CrossOrder="10" Kod="JPY" CurrencyCode="JPY">
    <Unit>100</Unit>
    <Isim>JAPON YENI</Isim>
    <CurrencyName>JAPENESE YEN</CurrencyName>
    <ForexBuying>27.50</ForexBuying>
    <ForexSelling>28.50</ForexSelling>
  </Currency>
  <Currency CrossOrder="11" Kod="XXX" CurrencyCode="XXX">
    <Unit>1</Unit>
    <Isim>BOS KUR</Isim>
    <CurrencyName>EMPTY RATE</CurrencyName>
    <ForexBuying></ForexBuying>
    <ForexSelling></ForexSelling>
  </Currency>
</Tarih_Date>
"""


def test_parse_tcmb_xml_midpoint():
    rates = parse_tcmb_xml(SAMPLE_XML)
    assert rates["USD"] == pytest.approx(41.20)  # среднее buying/selling
    assert rates["EUR"] == pytest.approx(46.50)


def test_parse_tcmb_xml_unit_scaling():
    rates = parse_tcmb_xml(SAMPLE_XML)
    assert rates["JPY"] == pytest.approx(0.28)  # котировка за 100 иен -> за 1


def test_parse_tcmb_xml_skips_empty():
    rates = parse_tcmb_xml(SAMPLE_XML)
    assert "XXX" not in rates


def test_parse_tcmb_xml_partial_quote():
    xml = SAMPLE_XML.replace("<ForexSelling>41.30</ForexSelling>", "<ForexSelling></ForexSelling>")
    rates = parse_tcmb_xml(xml)
    assert rates["USD"] == pytest.approx(41.10)  # доступна только одна сторона котировки
