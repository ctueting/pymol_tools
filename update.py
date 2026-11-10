def update(override=False, add_to_pymolrc=False):
  cmd.run("https://ctueting.github.io/pymol_tools/install.py")
  cmd.install(True,True)

cmd.extend("update_pymol_tools", update)
