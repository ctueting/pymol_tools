# This is an example of what one can do using PyMOL and Python.
# This code will download a structure, generate selections
# Identify the binding site, make distances
# And renderes a nice view

# As this is now a python script, we can use comments, function, and everything we learned in our Python session

# This DELETES EVERY OBJECT
# Just for debugging and to have a fresh start
cmd.delete('*')

# Load a molecule
cmd.fetch('1B38')

# create the selections, as in our example
cmd.select('protein_structure', '1B38 and polymer.protein')
cmd.select('ATP', '1B38 and resn ATP')
cmd.select('ion', '1B38 and resn MG')

# As a python script is more suitable for analysis, rather than representation
# we now want to do some coding

# We want extract all atoms from the ATP ligand
atom_list = []
cmd.iterate('ATP', 'atom_list.append(name)')

# now we want to iterate trough the ligand
# to find the residues, stabilizing the ligand
# we simplify an interaction by all non-carbon atoms

results = []

for atp_atom in atom_list:
    if atp_atom.startswith('C'):
        # we do not care for carbons
        continue

    # we now select all non-atp
    # non carbon atom around the given atom
    cmd.select('close', f'(atp and name {atp_atom} around 3.5) and not atp and not name C*')

    # get the atoms in the selection
    close_atoms = []
    cmd.iterate('close', 'close_atoms.append((resn, resi, chain, name))')

    if len(close_atoms) == 0:
        # no atom close
        continue

    # now, we not only want the atp, but also the exact distance
    for close_atom in close_atoms:
        resn, resi, chain, name = close_atom

        distance = cmd.get_distance(
            f'ATP and name {atp_atom}',
            f'chain {chain} and resi {resi} and name {name}'
        )

        # make an entry for the result
        entry = (atp_atom, chain, resn, resi, name, round(distance, 2))
        results.append(entry)

# print the results in the log
# As I "does not work, we need to use f-string formatting instead
print(f'{"ATPAtom":>8}{"Chain":>7}{"Resn":>7}{"Resi":>7}{"Atom":>7}{"Dist":>7}')
for entry in results:
    ATPAtom, Chain, Resn, Resi, Atom, Dist = entry
    print(f'{ATPAtom:>8}{Chain:>7}{Resn:>7}{Resi:>7}{Atom:>7}{Dist:>7.2f}')

# additionally, make a nice representation of the interaction network

# first, hide everything
cmd.hide('everything')

# show atp as sticks
cmd.show('sticks', 'atp')

# iterate again through the results
for entry in results:
    atp_atom, chain, resn, resi, name, _ = entry

    # show the interaction residue also as sticks
    if resn == "MG":
        cmd.show('spheres', f'chain {chain} and resi {resi}')
    elif resn == "HOH":
        cmd.show('spheres', f'chain {chain} and resi {resi}')
    else:
        cmd.show('sticks', f'chain {chain} and resi {resi}')

    # and draw a line between them
    cmd.distance(f'ATP and name {atp_atom}', f'chain {chain} and resi {resi} and name {name}')

# make the spheres smaller
cmd.set('sphere_scale', 0.4)

# and color them nicely
util.cbag('ATP')
util.cbag('polymer.protein')

# color the distance dashes in grey
cmd.color('grey', 'dist*')

# and hide the distance label from the distances
cmd.hide('labels')

# and zoom to the visible area
cmd.zoom('vis')

# And finally, render the image
cmd.run("https://ctueting.github.io/pymol_tools/tools.py")

signature()

cmd.ray(2000,2000)
cmd.png('ATP_binding.png')
