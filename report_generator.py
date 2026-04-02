"""
report_generator.py
Generates a professional A4 PDF report summarizing the BIPV solar assessment.
Uses fpdf2 for lightweight, dependency-free PDF generation.
"""

from fpdf import FPDF
from datetime import datetime
import io


class SolarReport(FPDF):
    """Custom PDF class with header and footer styling."""

    def __init__(self, title="Saurya Sankulan - BIPV Assessment Report"):
        super().__init__()
        self.report_title = title

    def header(self):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, self.report_title, border=False, align="L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, datetime.now().strftime("%Y-%m-%d %H:%M"), border=False, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    # --- Helper Methods ---

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 70, 130)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6, text)
        self.ln(2)

    def metric_row(self, metrics):
        """Render a row of metrics as styled boxes.
        metrics: list of (label, value, subtitle) tuples.
        """
        col_width = (self.w - 20) / len(metrics)
        start_x = self.get_x()
        start_y = self.get_y()
        box_h = 28

        for label, value, subtitle in metrics:
            # Background box
            self.set_fill_color(240, 245, 255)
            self.rect(self.get_x(), start_y, col_width - 3, box_h, style="F")

            # Value
            self.set_xy(self.get_x() + 4, start_y + 3)
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(30, 70, 130)
            self.cell(col_width - 10, 8, str(value))

            # Label
            self.set_xy(self.get_x() - (col_width - 10), start_y + 12)
            self.set_font("Helvetica", "", 9)
            self.set_text_color(80, 80, 80)
            self.cell(col_width - 10, 5, label)

            # Subtitle
            self.set_xy(self.get_x() - (col_width - 10), start_y + 18)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(140, 140, 140)
            self.cell(col_width - 10, 5, subtitle)

            # Move to next column
            self.set_xy(start_x + col_width * (metrics.index((label, value, subtitle)) + 1), start_y)

        self.set_y(start_y + box_h + 6)

    def data_table(self, headers, rows, col_widths=None):
        """Render a simple data table."""
        if col_widths is None:
            col_widths = [(self.w - 20) / len(headers)] * len(headers)

        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(30, 70, 130)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, h, border=1, fill=True, align="C")
        self.ln()

        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 50)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(248, 248, 248)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, str(cell), border=1, fill=True, align="C")
            self.ln()
        self.ln(4)


def generate_report(
    sim_date,
    num_buildings,
    study_radius_m,
    usable_area_pct,
    install_type,
    accuracy,
    total_kwh,
    homes_powered,
    total_co2,
    trees_equivalent,
    cars_off_road,
    profitable_buildings,
    top_buildings_df
):
    """
    Build the full PDF report and return it as bytes.

    Parameters
    ----------
    sim_date : str
        The date simulated.
    num_buildings : int
        Number of buildings analyzed.
    study_radius_m : int
        The study area radius in meters.
    usable_area_pct : float
        Usable roof area as a decimal (0-1).
    install_type : str
        Installation type string.
    accuracy : int
        Grid accuracy in meters.
    total_kwh : float
        Total energy in kWh.
    homes_powered : float
        Number of homes that could be powered.
    total_co2 : float
        CO2 offset in lbs.
    trees_equivalent : float
        Equivalent trees planted.
    cars_off_road : float
        Equivalent cars taken off the road.
    profitable_buildings : int
        Buildings with sufficient solar potential.
    top_buildings_df : list of tuples
        List of (building_id, kWh) for top buildings.

    Returns
    -------
    bytes
        The generated PDF as bytes ready for download.
    """
    pdf = SolarReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- Title Block ---
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 70, 130)
    pdf.cell(0, 14, "Solar Energy Assessment Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"Simulation Date: {sim_date}  |  Study Radius: {study_radius_m}m  |  Buildings Analyzed: {num_buildings}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # --- Summary ---
    pdf.section_title("Summary")
    pdf.metric_row([
        ("Total Solar Potential", f"{total_kwh:,.0f} kWh", "Daily Generation"),
        ("Homes Powered", f"{homes_powered:,.0f}", "Equivalent Avg. Homes"),
        ("CO2 Offset", f"{total_co2:,.0f} lbs", "Daily Carbon Reduction"),
    ])
    pdf.metric_row([
        ("Trees Equivalent", f"{trees_equivalent:,.0f}", "Annual Planting Impact"),
        ("Cars Off the Road", f"{cars_off_road:,.1f}", "Daily Emission Equivalent"),
        ("Viable Buildings", f"{profitable_buildings}/{num_buildings}", "With Profitable Potential"),
    ])

    # --- Simulation Parameters ---
    pdf.section_title("Simulation Parameters")
    pdf.body_text(
        f"Grid Accuracy: {accuracy}m  |  "
        f"Usable Roof Area: {usable_area_pct*100:.0f}%  |  "
        f"Installation Type: {install_type}  |  "
        f"PV Efficiency: 18%  |  Performance Ratio: 75%"
    )

    # --- Top Buildings Table ---
    pdf.section_title("Top 10 High-Yield Buildings")
    headers = ["Rank", "Building ID", "Daily Energy (kWh)"]
    rows = []
    for rank, (bid, kwh) in enumerate(top_buildings_df, 1):
        rows.append((str(rank), str(bid), f"{kwh:,.2f}"))
    pdf.data_table(headers, rows, col_widths=[20, 80, 90])

    # --- Methodology ---
    pdf.section_title("Methodology")
    pdf.body_text(
        "This assessment uses the PyBDShadow engine to simulate solar irradiance on building rooftops "
        "based on LOD-1 (Level of Detail 1) 3D city models. The engine calculates shadow casting from "
        "neighboring structures across an entire day to determine the total hours of direct sunlight "
        "received by each grid point on every roof surface.\n\n"
        "Energy output is estimated using the formula:\n"
        "  E = Hours x Area x Efficiency (18%) x Performance Ratio (0.75) x Yield Multiplier\n\n"
        "The Usable Roof Area percentage accounts for real-world constraints including HVAC equipment, "
        "structural setbacks, maintenance access paths, and shading from parapets. "
        "The Optimal Tilt multiplier (+15%) applies an industry-accepted heuristic for mid-latitude "
        "locations where angling panels toward the equator increases annual yield."
    )

    # --- Disclaimer ---
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 4,
        "Disclaimer: This report is generated for academic and research purposes. "
        "Actual solar energy output depends on local weather, panel specifications, "
        "shading from vegetation, and other site-specific factors not modeled here."
    )

    # Return as bytes
    return bytes(pdf.output())
