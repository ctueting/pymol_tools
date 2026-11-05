def color_plddt(selection="all"):
    plddt_bins = [
        (0, 50, "0xFF7D45"),     # Orange
        (50, 70, "0xFFDB13"),    # Yellow
        (70, 90, "0x65CBF3"),    # Light blue
        (90, 101, "0x0053D6")    # Dark blue
    ]

    # Validate B-factors
    x = cmd.count_atoms(f"({selection}) and (b > 100 or b < 0)")

    if x != 0:
        print(f"Warning: {x} atoms have B-factors outside 0–100 in selection '{selection}'.")
        return

    for lower, upper, color in plddt_bins:
        cmd.color(color, f"({selection}) and not (b < {lower}) and b < {upper}")


cmd.extend("color_plddt", color_plddt)
