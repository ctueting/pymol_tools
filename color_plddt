def color_plddt(selection="all"):
    plddt_bins = [
        (0, 50, "0xE08155"),
        (50, 70, "0xF9DC4D"),
        (70, 90, "0x7FC8ED"),
        (90, 101, "0x37569D")
    ]

    # Validate B-factors
    x = cmd.count_atoms(f"({selection}) and (b > 100 or b < 0)")

    if x != 0:
        print(f"Warning: {x} atoms have B-factors outside 0–100 in selection '{selection}'.")
        return

    for lower, upper, color in plddt_bins:
        cmd.color(color, f"({selection}) and not (b < {lower}) and b < {upper}")


cmd.extend("color_plddt", color_plddt)
