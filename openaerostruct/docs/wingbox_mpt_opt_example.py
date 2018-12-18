from __future__ import division, print_function

# Ignore the #docs section begin/end comments. They are just used to split up the code for the documentation webpage.
#docs section 0 begin

import numpy as np
from openaerostruct.geometry.utils import generate_mesh
from openaerostruct.integration.aerostruct_groups import AerostructGeometry, AerostructPoint
from openmdao.api import IndepVarComp, Problem, ScipyOptimizeDriver, SqliteRecorder, ExecComp
from openaerostruct.structures.wingbox_fuel_vol_delta import WingboxFuelVolDelta
from openaerostruct.utils.constants import grav_constant

#docs section 0 end

#docs section 1 begin

# Provide coordinates for a portion of an airfoil for the wingbox cross-section as an nparray with dtype=complex (to work with the complex-step approximation for derivatives).
# These should be for an airfoil with the chord scaled to 1.
# We use the 10% to 60% portion of the NASA SC2-0612 airfoil for this case
# We use the coordinates available from airfoiltools.com. Using such a large number of coordinates is not necessary.
# The first and last x-coordinates of the upper and lower surfaces must be the same

upper_x = np.array([0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.3, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.5, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6], dtype = 'complex128')
lower_x = np.array([0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.2, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.3, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.5, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.6], dtype = 'complex128')
upper_y = np.array([ 0.0447,  0.046,  0.0472,  0.0484,  0.0495,  0.0505,  0.0514,  0.0523,  0.0531,  0.0538, 0.0545,  0.0551,  0.0557, 0.0563,  0.0568, 0.0573,  0.0577,  0.0581,  0.0585,  0.0588,  0.0591,  0.0593,  0.0595,  0.0597,  0.0599,  0.06,    0.0601,  0.0602,  0.0602,  0.0602,  0.0602,  0.0602,  0.0601,  0.06,    0.0599,  0.0598,  0.0596,  0.0594,  0.0592,  0.0589,  0.0586,  0.0583,  0.058,   0.0576,  0.0572,  0.0568,  0.0563,  0.0558,  0.0553,  0.0547,  0.0541], dtype = 'complex128')
lower_y = np.array([-0.0447, -0.046, -0.0473, -0.0485, -0.0496, -0.0506, -0.0515, -0.0524, -0.0532, -0.054, -0.0547, -0.0554, -0.056, -0.0565, -0.057, -0.0575, -0.0579, -0.0583, -0.0586, -0.0589, -0.0592, -0.0594, -0.0595, -0.0596, -0.0597, -0.0598, -0.0598, -0.0598, -0.0598, -0.0597, -0.0596, -0.0594, -0.0592, -0.0589, -0.0586, -0.0582, -0.0578, -0.0573, -0.0567, -0.0561, -0.0554, -0.0546, -0.0538, -0.0529, -0.0519, -0.0509, -0.0497, -0.0485, -0.0472, -0.0458, -0.0444], dtype = 'complex128')

#docs section 1 end

#docs section 2 begin

# Create a dictionary to store options about the surface
mesh_dict = {'num_y' : 15,
             'num_x' : 3,
             'wing_type' : 'uCRM_based',
             'symmetry' : True,
             'chord_cos_spacing' : 0,
             'span_cos_spacing' : 0,
             'num_twist_cp' : 4
             }

mesh, twist_cp = generate_mesh(mesh_dict)

#docs section 2 end

#docs section 3 begin

surf_dict = {
            # Wing definition
            'name' : 'wing',         # give the surface some name
            'symmetry' : True,       # if True, model only one half of the lifting surface
            'S_ref_type' : 'projected', # how we compute the wing area,
                                     # can be 'wetted' or 'projected'
            'mesh' : mesh,

            'fem_model_type' : 'wingbox', # 'wingbox' or 'tube'
            'data_x_upper' : upper_x,
            'data_x_lower' : lower_x,
            'data_y_upper' : upper_y,
            'data_y_lower' : lower_y,

            #docs section 3 end

            #docs section 4 begin

            'twist_cp' : np.array([4., 5., 8., 9.]), # [deg]

            'spar_thickness_cp' : np.array([0.004, 0.005, 0.008, 0.01]), # [m]
            'skin_thickness_cp' : np.array([0.005, 0.01, 0.015, 0.025]), # [m]

            't_over_c_cp' : np.array([0.08, 0.08, 0.10, 0.08]),
            'original_wingbox_airfoil_t_over_c' : 0.12,

            #docs section 4 end

            #docs section 5 begin

            # Aerodynamic deltas.
            # These CL0 and CD0 values are added to the CL and CD
            # obtained from aerodynamic analysis of the surface to get
            # the total CL and CD.
            # These CL0 and CD0 values do not vary wrt alpha.
            # They can be used to account for things that are not included, such as contributions from the fuselage, camber, etc.
            'CL0' : 0.0,            # CL delta
            'CD0' : 0.0078,         # CD delta

            'with_viscous' : True,  # if true, compute viscous drag
            'with_wave' : True,     # if true, compute wave drag

            # Airfoil properties for viscous drag calculation
            'k_lam' : 0.05,         # fraction of chord with laminar
                                    # flow, used for viscous drag
            'c_max_t' : .38,       # chordwise location of maximum thickness

            #docs section 5 end

            #docs section 6 begin

            # Structural values are based on aluminum 7075
            'E' : 73.1e9,              # [Pa] Young's modulus
            'G' : (73.1e9/2/1.33),     # [Pa] shear modulus (calculated using E and the Poisson's ratio here)
            'yield' : (420.e6 / 1.5),  # [Pa] allowable yield stress
            'mrho' : 2.78e3,           # [kg/m^3] material density
            'strength_factor_for_upper_skin' : 1.0, # the yield stress is multiplied by this factor for the upper skin

            'wing_weight_ratio' : 1.25,
            'exact_failure_constraint' : False, # if false, use KS function

            #docs section 6 end

            #docs section 7 begin

            'struct_weight_relief' : True,
            'distributed_fuel_weight' : True,

            #docs section 7 end

            #docs section 8 begin

            'fuel_density' : 803.,      # [kg/m^3] fuel density (only needed if the fuel-in-wing volume constraint is used)
            'Wf_reserve' :15000.,       # [kg] reserve fuel mass

            }

surfaces = [surf_dict]

#docs section 8 end

#docs section 9 begin

# Create the problem and assign the model group
prob = Problem()

# Add problem information as an independent variables component
indep_var_comp = IndepVarComp()
indep_var_comp.add_output('Mach_number', val=np.array([0.85, 0.64]))
indep_var_comp.add_output('v', val=np.array([.85 * 295.07, .64 * 340.294]), units='m/s')
indep_var_comp.add_output('re',val=np.array([0.348*295.07*.85*1./(1.43*1e-5), \
                          1.225*340.294*.64*1./(1.81206*1e-5)]),  units='1/m')
indep_var_comp.add_output('rho', val=np.array([0.348, 1.225]), units='kg/m**3')
indep_var_comp.add_output('speed_of_sound', val= np.array([295.07, 340.294]), units='m/s')

#docs section 9 end

#docs section 10 begin

indep_var_comp.add_output('CT', val=0.53/3600, units='1/s')
indep_var_comp.add_output('R', val=14.307e6, units='m')
indep_var_comp.add_output('W0', val=148000 + surf_dict['Wf_reserve'],  units='kg')

#docs section 10 end

#docs section 11 begin

indep_var_comp.add_output('load_factor', val=np.array([1., 2.5]))
indep_var_comp.add_output('alpha', val=0., units='deg')
indep_var_comp.add_output('alpha_maneuver', val=0., units='deg')

indep_var_comp.add_output('empty_cg', val=np.zeros((3)), units='m')

#docs section 11 end

#docs section 12 begin

indep_var_comp.add_output('fuel_mass', val=10000., units='kg')

prob.model.add_subsystem('prob_vars',
     indep_var_comp,
     promotes=['*'])

#docs section 12 end

#docs section 13 begin

# Loop over each surface in the surfaces list
for surface in surfaces:

    # Get the surface name and create a group to contain components
    # only for this surface
    name = surface['name']

    aerostruct_group = AerostructGeometry(surface=surface)

    # Add groups to the problem with the name of the surface.
    prob.model.add_subsystem(name, aerostruct_group)

#docs section 13 end

#docs section 14 begin

# Loop through and add a certain number of aerostruct points
for i in range(2):

    point_name = 'AS_point_{}'.format(i)
    # Connect the parameters within the model for each aero point

    # Create the aerostruct point group and add it to the model
    AS_point = AerostructPoint(surfaces=surfaces, internally_connect_fuelburn=False)

    prob.model.add_subsystem(point_name, AS_point)

    #docs section 14 end

    #docs section 15 begin

    # Connect flow properties to the analysis point
    prob.model.connect('v', point_name + '.v', src_indices=[i])
    prob.model.connect('Mach_number', point_name + '.Mach_number', src_indices=[i])
    prob.model.connect('re', point_name + '.re', src_indices=[i])
    prob.model.connect('rho', point_name + '.rho', src_indices=[i])
    prob.model.connect('CT', point_name + '.CT')
    prob.model.connect('R', point_name + '.R')
    prob.model.connect('W0', point_name + '.W0')
    prob.model.connect('speed_of_sound', point_name + '.speed_of_sound', src_indices=[i])
    prob.model.connect('empty_cg', point_name + '.empty_cg')
    prob.model.connect('load_factor', point_name + '.load_factor', src_indices=[i])
    prob.model.connect('fuel_mass', point_name + '.total_perf.L_equals_W.fuelburn')
    prob.model.connect('fuel_mass', point_name + '.total_perf.CG.fuelburn')

    #docs section 15 end

    #docs section 16 begin

    for surface in surfaces:

        name = surface['name']

        if surf_dict['distributed_fuel_weight']:
            prob.model.connect('load_factor', point_name + '.coupled.load_factor', src_indices=[i])

        com_name = point_name + '.' + name + '_perf.'
        prob.model.connect(name + '.local_stiff_transformed', point_name + '.coupled.' + name + '.local_stiff_transformed')
        prob.model.connect(name + '.nodes', point_name + '.coupled.' + name + '.nodes')

        # Connect aerodyamic mesh to coupled group mesh
        prob.model.connect(name + '.mesh', point_name + '.coupled.' + name + '.mesh')
        if surf_dict['struct_weight_relief']:
            prob.model.connect(name + '.element_mass', point_name + '.coupled.' + name + '.element_mass')

        # Connect performance calculation variables
        prob.model.connect(name + '.nodes', com_name + 'nodes')
        prob.model.connect(name + '.cg_location', point_name + '.' + 'total_perf.' + name + '_cg_location')
        prob.model.connect(name + '.structural_mass', point_name + '.' + 'total_perf.' + name + '_structural_mass')

        # Connect wingbox properties to von Mises stress calcs
        prob.model.connect(name + '.Qz', com_name + 'Qz')
        prob.model.connect(name + '.J', com_name + 'J')
        prob.model.connect(name + '.A_enc', com_name + 'A_enc')
        prob.model.connect(name + '.htop', com_name + 'htop')
        prob.model.connect(name + '.hbottom', com_name + 'hbottom')
        prob.model.connect(name + '.hfront', com_name + 'hfront')
        prob.model.connect(name + '.hrear', com_name + 'hrear')

        prob.model.connect(name + '.spar_thickness', com_name + 'spar_thickness')
        prob.model.connect(name + '.t_over_c', com_name + 't_over_c')

        #docs section 16 end

#docs section 17 begin

prob.model.connect('alpha', 'AS_point_0' + '.alpha')
prob.model.connect('alpha_maneuver', 'AS_point_1' + '.alpha')

#docs section 17 end

#docs section 18 begin

# Here we add the fuel volume constraint componenet to the model
prob.model.add_subsystem('fuel_vol_delta', WingboxFuelVolDelta(surface=surface))
prob.model.connect('wing.struct_setup.fuel_vols', 'fuel_vol_delta.fuel_vols')
prob.model.connect('AS_point_0.fuelburn', 'fuel_vol_delta.fuelburn')

if surf_dict['distributed_fuel_weight']:
    prob.model.connect('wing.struct_setup.fuel_vols', 'AS_point_0.coupled.wing.struct_states.fuel_vols')
    prob.model.connect('fuel_mass', 'AS_point_0.coupled.wing.struct_states.fuel_mass')

    prob.model.connect('wing.struct_setup.fuel_vols', 'AS_point_1.coupled.wing.struct_states.fuel_vols')
    prob.model.connect('fuel_mass', 'AS_point_1.coupled.wing.struct_states.fuel_mass')

#docs section 18 end

#docs section 19 begin

comp = ExecComp('fuel_diff = (fuel_mass - fuelburn) / fuelburn')
prob.model.add_subsystem('fuel_diff', comp,
    promotes_inputs=['fuel_mass'],
    promotes_outputs=['fuel_diff'])
prob.model.connect('AS_point_0.fuelburn', 'fuel_diff.fuelburn')

#docs section 19 end

#docs section 20 begin

prob.model.add_objective('AS_point_0.fuelburn', scaler=1e-5)

prob.model.add_design_var('wing.twist_cp', lower=-15., upper=15., scaler=0.1)
prob.model.add_design_var('wing.spar_thickness_cp', lower=0.003, upper=0.1, scaler=1e2)
prob.model.add_design_var('wing.skin_thickness_cp', lower=0.003, upper=0.1, scaler=1e2)
prob.model.add_design_var('wing.geometry.t_over_c_cp', lower=0.07, upper=0.2, scaler=10.)
prob.model.add_design_var('alpha_maneuver', lower=-15., upper=15)

#docs section 20 end

#docs section 21 begin

prob.model.add_constraint('AS_point_0.CL', equals=0.5)

#docs section 21 end

#docs section 22 begin

prob.model.add_constraint('AS_point_1.L_equals_W', equals=0.)
prob.model.add_constraint('AS_point_1.wing_perf.failure', upper=0.)

#docs section 22 end

#docs section 23 begin

prob.model.add_constraint('fuel_vol_delta.fuel_vol_delta', lower=0.)

#docs section 23 end

#docs section 24 begin

prob.model.add_design_var('fuel_mass', lower=0., upper=2e5, scaler=1e-5)
prob.model.add_constraint('fuel_diff', equals=0.)

#docs section 24 end

#docs section 25 begin

prob.driver = ScipyOptimizeDriver()
prob.driver.options['optimizer'] = 'SLSQP'
prob.driver.options['tol'] = 1e-2

#docs section 25 end

#docs section 26 begin

recorder = SqliteRecorder("aerostruct.db")
prob.driver.add_recorder(recorder)

# We could also just use prob.driver.recording_options['includes']=['*'] here, but for large meshes the database file becomes extremely large. So we just select the variables we need.
prob.driver.recording_options['includes'] = \
['prob_vars.alpha', 'prob_vars.rho', 'prob_vars.v', 'prob_vars.cg', \
'AS_point_1.total_perf.CG.cg', 'AS_point_0.total_perf.CG.cg', \
'AS_point_0.coupled.wing_loads.loads', 'AS_point_1.coupled.wing_loads.loads', \
'wing.wingbox_group.skin_thickness_bsp.skin_thickness', \
'wing.geometry.mesh.rotate.mesh',\
'wing.wingbox_group.spar_thickness_bsp.spar_thickness', \
'wing.wingbox_group.spar_thickness_bsp.spar_thickness', \
'wing.geometry.t_over_c_bsp.t_over_c', \
'AS_point_0.wing_perf.struct_funcs.vonmises.vonmises', \
'AS_point_1.wing_perf.struct_funcs.vonmises.vonmises', \
'wing.struct_setup.structural_mass.structural_mass', \
'AS_point_0.coupled.wing.def_mesh.displacement_transfer.def_mesh', \
'AS_point_1.coupled.wing.def_mesh.displacement_transfer.def_mesh', \
'AS_point_0.coupled.wing.aero_geom.normals', \
'AS_point_1.coupled.wing.aero_geom.normals', \
'AS_point_0.coupled.wing.aero_geom.widths',  'AS_point_1.coupled.wing.aero_geom.widths', \
'AS_point_0.coupled.aero_states.panel_forces_surf.wing_sec_forces', \
'AS_point_1.coupled.aero_states.panel_forces_surf.wing_sec_forces', \
'AS_point_0.wing_perf.aero_funcs.coeffs.CL1', 'AS_point_1.wing_perf.aero_funcs.coeffs.CL1', \
'AS_point_0.coupled.wing.aero_geom.S_ref',
'AS_point_1.coupled.wing.aero_geom.S_ref',
'wing.geometry.twist_bsp.twist']

prob.driver.recording_options['record_objectives'] = True
prob.driver.recording_options['record_constraints'] = True
prob.driver.recording_options['record_desvars'] = True
prob.driver.recording_options['record_inputs'] = True

#docs section 26 end

#docs section 27 begin

# Set up the problem
prob.setup()

# from openmdao.api import view_model
# view_model(prob)

# prob.check_partials(form='central', compact_print=True)

prob.run_driver()

print('The fuel burn value is', prob['AS_point_0.fuelburn'][0], '[kg]')
print('The wingbox mass (excluding the wing_weight_ratio) is', prob['wing.structural_mass'][0]/grav_constant/surf_dict['wing_weight_ratio'], '[kg]')

#docs section 27 end
