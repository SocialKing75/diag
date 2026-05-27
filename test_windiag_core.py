from windiag_core import (
    Dossier,
    Room,
    Surface,
    build_car_from_template,
    extract_car_summary,
    format_recap,
    parse_surface,
    read_car_fields,
    write_car_fields,
)


def test_parse_surface_accepts_comma_and_material() -> None:
    surface = parse_surface("18,4 m² parquet")

    assert surface == Surface(area_m2=18.4, material="parquet")


def test_parse_surface_accepts_area_only() -> None:
    surface = parse_surface("42")

    assert surface == Surface(area_m2=42, material=None)


def test_format_recap_includes_totals() -> None:
    dossier = Dossier(
        name="Maison Dupont",
        created_at="2026-05-27T10:00:00",
        rooms=[
            Room(
                name="Salon",
                floor=Surface(18.4, "parquet"),
                walls=Surface(42, "placo"),
                ceiling=Surface(18.4, "peinture"),
                height_m=2.5,
                orientation="Sud",
                joinery="2 fenêtres PVC",
            )
        ],
    )

    recap = format_recap(dossier)

    assert "Dossier : Maison Dupont" in recap
    assert "Sol : 18.4 m²" in recap
    assert "Murs : 42 m²" in recap
    assert "Plafonds : 18.4 m²" in recap


def test_car_roundtrip_preserves_cp1252_crlf_and_embedded_newlines(tmp_path) -> None:
    path = tmp_path / "modele.CAR"
    fields = ["Wincarez 8.0", "GÉNÉRALI", "{\\rtf1\\ansi\r\nPLAN\r\n}"]

    write_car_fields(path, fields)

    raw = path.read_bytes()
    assert b"\r\n" in raw
    assert "GÉNÉRALI".encode("cp1252") in raw
    assert read_car_fields(path) == fields


def test_extract_car_summary_and_build_from_template(tmp_path) -> None:
    template = tmp_path / "template.CAR"
    output = tmp_path / "sortie.CAR"
    fields = [""] * 90
    fields[0] = "Wincarez 8.0"
    fields[1] = "Ancien donneur"
    fields[5] = "01/01/2026"
    fields[25] = "ANCIENNE RUE"
    write_car_fields(template, fields)

    build_car_from_template(
        template,
        {
            "donneur_ordre": "GENERALI VIE",
            "date_commande": "30/01/2026",
            "bien_rue": "INGRES",
        },
        output,
    )

    summary = extract_car_summary(output)
    assert summary["logiciel"] == "Wincarez 8.0"
    assert summary["donneur_ordre"] == "GENERALI VIE"
    assert summary["date_commande"] == "30/01/2026"
    assert summary["bien_rue"] == "INGRES"
