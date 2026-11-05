# ray signature v2 by Christian Tueting (c) 2022
SIGNATURE_TOGGLE = False
def render_signature():
    global SIGNATURE_TOGGLE
    
    if not SIGNATURE_TOGGLE:
        cmd.set("ray_trace_gain",1)
        cmd.set("antialias",1)
        cmd.set("antialias_shader",2)
        cmd.set("cartoon_flat_sheets",1)
        cmd.set("cartoon_flat_cycles",5)
        cmd.set("cartoon_rect_width",0.25)
        cmd.set("cartoon_gap_cutoff",10)
        cmd.set("cartoon_smooth_loops",0)
        cmd.set("cartoon_loop_radius",0.2)
        cmd.set("ray_trace_color",[0.1,0.1,0.1])
        cmd.set("cartoon_fancy_helices",1)
        cmd.set("cartoon_dumbbell_radius",0.2)
        cmd.set("cartoon_dumbbell_length",1.75)
        cmd.set("cartoon_dumbbell_width",0)
        cmd.set("ambient",0.6)
        cmd.set("cartoon_rect_length",1.5)
        cmd.set("ray_trace_mode",1)
        cmd.set("cartoon_oval_length",0.3)
        cmd.set("cartoon_oval_width",1)
        cmd.set("ray_trace_slope_factor",1)
        cmd.set("ray_trace_disco_factor",2)
        cmd.set("cartoon_side_chain_helper","on")
        cmd.bg_color("white")
        cmd.set("ray_opaque_background",1)
        SIGNATURE_TOGGLE = True
    else:
        #default values
        cmd.set("ray_trace_gain",0.12000)
        cmd.set("antialias",1)
        cmd.set("cartoon_flat_sheets","on")
        cmd.set("cartoon_flat_cycles",4)
        cmd.set("cartoon_rect_width",0.40000)
        cmd.set("cartoon_gap_cutoff",10)
        cmd.set("cartoon_smooth_loops","off")
        cmd.set("cartoon_loop_radius",0.20000)
        cmd.set("ray_trace_color","front")
        cmd.set("cartoon_fancy_helices","off")
        cmd.set("cartoon_dumbbell_radius",0.16000)
        cmd.set("cartoon_dumbbell_length",1.60000)
        cmd.set("cartoon_dumbbell_width",0.17000)
        cmd.set("ambient",0.14000)
        cmd.set("cartoon_rect_length",1.40000)
        cmd.set("ray_trace_mode",0)
        cmd.set("cartoon_oval_length",1.35000)
        cmd.set("cartoon_oval_width",0.25000)
        cmd.set("ray_trace_slope_factor",0.60000)
        cmd.set("ray_trace_disco_factor",0.05000)
        cmd.set("cartoon_side_chain_helper","off")
        cmd.set("ray_opaque_background",-1)
        cmd.bg_color("black")
        SIGNATURE_TOGGLE = False

cmd.extend("signature", render_signature)
