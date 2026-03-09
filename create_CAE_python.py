# -*- coding: utf-8 -*-
from abaqus import *
from abaqusConstants import *
import sys

sys.path.append('.')   # ensures current dir is in path for utils.py
from abaqus_functions import (concrete_param,compression_curve,tension_curve,cfrp_properties, create_nset_from_surface)

save_cae = False
export_inp = True
path = '../CAE/base_models/251117-concrete_param' # 251311-tendon_distance
file_name = '250923-CAE_Python_c2.5_full_base_model' # '251113-CAE_python_sp3.0_base_model'  # without f_cm
cae_infile = '{}/{}.cae'.format(path, file_name)

# Parameter
f_cm_cube = 70  # Compressive strength of concrete cube [MPa]
cae_outfile = '{}/{}_fcm{}.cae'.format(path, file_name, f_cm_cube)
inp_CAE_outfile = '{}/{}_fcm{}_Ecm22.inp'.format(path, file_name, f_cm_cube)

mdb = openMdb(cae_infile)
model = mdb.models['Model-1']

# --- Concrete Material, Section, Assignment ---
f_cm, f_ck, f_ctm, E_cm = concrete_param(f_cm_cube)
hardening, damage = compression_curve(f_cm=f_cm, E_cm=E_cm)
tens = tension_curve(f_cm, f_ctm)

mat = model.Material(name='Concrete')
mat.Density(table=((2.4e-09,),))
mat.Elastic(table=((E_cm, 0.2),))
mat.ConcreteDamagedPlasticity(table=((31., 0.1, 1.16, 0.667, 0.0001), ))

# The suboptions go under .concreteDamagedPlasticity
mat.concreteDamagedPlasticity.ConcreteCompressionHardening(table=hardening)
mat.concreteDamagedPlasticity.ConcreteCompressionDamage(table=damage)
mat.concreteDamagedPlasticity.ConcreteTensionStiffening(table=[(s, w) for s, w, d in tens], type=DISPLACEMENT)
mat.concreteDamagedPlasticity.ConcreteTensionDamage(table=[(d, w) for s, w, d in tens], type=DISPLACEMENT)

# Create a section for the concrete material
model.HomogeneousSolidSection(name='ConcreteSection', material='Concrete', thickness=None)
part_conc = model.parts['ConcreteBody']
region_conc = part_conc.Set(cells=part_conc.cells[:], name='ConcreteRegion')
part_conc.SectionAssignment(region=region_conc, sectionName='ConcreteSection')

# --- CFRP Strand Material, Section, Assignment ---
E1, E2, E3, nu12, nu13, nu23, G12, G13, G23, density = cfrp_properties()
mat2 = model.Material(name='CFRPStrand')
mat2.Density(table=((density, ),  ))
mat2.Elastic(type=ENGINEERING_CONSTANTS, table=((E1, E2, E3, nu12, nu13, nu23, G12, G13, G23), ))
model.HomogeneousSolidSection(name='StrandSection', material='CFRPStrand')
part_strand = model.parts['CFRPStrand']
region_strand = part_strand.Set(cells=part_strand.cells[:], name='StrandRegion')
part_strand.SectionAssignment(region=region_strand, sectionName='StrandSection')
# --- Assign Material Orientation for CFRP Strand ---
# Define a local coordinate system with X (axis 1) aligned to the fiber (e.g., global Z)
part_strand.DatumCsysByThreePoints(name='FiberCSYS',
    coordSysType=CARTESIAN,
    origin=(0.0, 0.0, 0.0),
    point1=(0.0, 0.0, 1.0),  # Fiber direction along Z
    point2=(0.0, 1.0, 0.0))  # Defines plane for orientation

datum_csys_id = part_strand.datums.keys()[-1]

part_strand.assignMaterialOrientation(
    region=region_strand,
    orientationType=SYSTEM,
    axis=AXIS_1,
    localCsys=part_strand.datums[datum_csys_id],
    fieldName='',
    additionalRotationType=ROTATION_NONE,
    angle=0.0,
    stackDirection=STACK_3)

assembly = model.rootAssembly

#surf_left = assembly.instances['ConcreteBody-1'].surfaces['Surf_left']
#all_nodes = set()
#for face in surf_left.faces:
#    nodes = face.getNodes()
#    if nodes:  # Only add if not None
#        all_nodes.update(nodes)

#if all_nodes:
#    assembly.Set(name='Nset_left', nodes=list(all_nodes))
#    print("Nset_left created with {} nodes".format(len(all_nodes)))
#else:
#    print("Warning: No nodes found for Surf_left in ConcreteBody-1")


if save_cae:
    mdb.saveAs(pathName=cae_outfile)
    print("Model saved as {}".format(cae_outfile))

if export_inp:
    # You must create a Job to export the inp file
    job_name = 'export_job'
    mdb.Job(name=job_name, model='Model-1')
    # Optionally, change working directory or use the default (writes as 'export_job.inp')
    mdb.jobs[job_name].writeInput()
    print("Input file exported as {} (default: export_job.inp)".format(inp_CAE_outfile))
    # Move/rename the file if you want:
    import shutil, os
    if os.path.exists(job_name + '.inp'):
        shutil.move(job_name + '.inp', inp_CAE_outfile)
        print("Input file renamed to {}".format(inp_CAE_outfile))
