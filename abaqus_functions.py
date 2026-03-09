# -*- coding: utf-8 -*-
from traceback import print_tb

import numpy as np
# from __future__ import division, print_function

from numpy.testing.print_coercion_tables import print_coercion_table


def concrete_param(f_cm_cube):
    f_cm = 0.84 * f_cm_cube
    f_ck = f_cm - 8.0
    if f_cm_cube > 70:
        f_ctm = 2.12 *np.log(1.0 + (f_cm/10.0))
        E_cm = 19000.0 * (f_cm / 10.0) ** 0.3
    else:
        f_ctm = 0.25 * f_ck ** (2.0 / 3.0)
        E_cm = 22000.0 * (f_cm / 10.0) ** 0.3
    return f_cm, f_ck, f_ctm, E_cm



def compression_curve(f_cm, E_cm, print_table=True):
    import numpy as np
    fcm_t28 = 0.84 * 82.2
    eps_c1_t28 = 0.7 * fcm_t28 ** 0.31 / 1000.0
    eps_cu_t28 = 2.8 + 27 * ((98.0 - fcm_t28) / 100.0) ** 4

    E_c0 = 1.05 * E_cm
    if f_cm > 70:
        eps_c1 = 0.7e-3 * (f_cm ** 0.31)
        eps_cu = 0.0026 + 35.0 * ((max(0.0, 90.0 - f_cm)) / 1000.0) ** 4
        eps_cu = float(np.clip(eps_cu, 0.0026, 0.0035))
    else:
        eps_c1 = (0.44 * f_cm ** (1.0 / 3.0) + 2.1 * f_cm ** (-1.0 / 2.0)) / 1000.0
        eps_cu = min((2.6 + 0.035 * (98.0 - f_cm)) / 1000.0, 3.5 / 1000.0)
    k = 1.05 * E_cm * eps_c1 / f_cm

    print("eps_c1 = {:10.6f} (MPa)".format(eps_c1))
    print("eps_cu = {:10.6f} (MPa)".format(eps_cu))
    print("E_c0 = {:10.6f} (MPa)".format(E_c0))
    print("k = {:10.6f}".format(k))

    eps_yield = 0.4 * f_cm / E_cm
    eps_c = list(np.linspace(eps_yield, eps_c1, 10))
    eps_c += list(np.linspace(eps_c1 + 0.0001, eps_cu, 3))

    # Manually find first point after eps_c1
    index_eps_c1 = None
    for i, val in enumerate(eps_c):
        if val > eps_c1:
            index_eps_c1 = i
            break

    if index_eps_c1 is not None:
        eps_c = eps_c[:index_eps_c1 + 1]

    data = []
    damage_data = [(0.0, 0.0)]
    for eps in eps_c:
        eta = eps / eps_c1
        numerator = k * eta - eta ** 2
        denominator = 1 + (k - 2) * eta
        sigma = numerator / denominator * f_cm
        eps_el = sigma / E_c0
        eps_in = eps - eps_el
        damage = 0.0 if eps < eps_c1 else 1.0 - sigma / f_cm
        damage = min(damage, 0.9999)

        if len(data) == 0:
            eps_in = 0.0  # enforce zero inelastic strain at start

        data.append((sigma, eps_in))
        if damage != 0.0:
            damage_data.append((eps_in, damage))

    if print_table:
        print("\n*** Compression Curve Data (for ABAQUS Hardening) ***")
        print("** Stress (MPa), Inelastic Strain")
        for sigma, eps_in in data:
            print("{:.4f}, {:.6f}".format(sigma, eps_in))

        print("\n** Damage Evolution Curve:")
        print("** Inelastic Strain, Damage")
        for eps_in, damage in damage_data:
            print("{:.6f}, {:.6f}".format(eps_in, damage))

    return data, damage_data


def tension_curve(f_cm, f_ctm, smooth_tail=True):
    import numpy as np
    import matplotlib.pyplot as plt

    G_f = 0.03 * (f_cm / 10) ** 0.7
    w_c = 2 * G_f / f_ctm
    w_t = np.linspace(0, w_c, 20)
    sigma_t = f_ctm * np.exp(-(f_ctm / G_f) * w_t)
    min_sigma = 0.01 * f_ctm
    valid_idx = np.where(sigma_t >= min_sigma)[0]
    w_t = w_t[valid_idx]
    sigma_t = sigma_t[valid_idx]
    if smooth_tail and len(w_t) >= 2:
        w_last = w_t[-1]
        s_last = sigma_t[-1]
        s_tail = np.linspace(s_last, min_sigma, 3)[1:]
        w_tail = w_last + np.linspace(0.01, 0.03, len(s_tail)) * w_c
        sigma_t = np.concatenate((sigma_t, s_tail))
        w_t = np.concatenate((w_t, w_tail))
    damage = 1 - sigma_t / f_ctm
    damage = np.clip(damage, 0.0, 0.9999)

    return list(zip(sigma_t, w_t, damage))

def cfrp_properties():
    E1 = 116607 # 130599.7 # 116607 # 97950
    E2 = 8800
    E3 = 8800
    nu12 = 0.3
    nu13 = 0.3
    nu23 = 0.47
    G12 = 6200
    G13 = 6200
    G23 = 7143
    density = 1.53e-09
    return E1, E2, E3, nu12, nu13, nu23, G12, G13, G23, density


# --- Create NSETS from ASSEMBLY SURFACES for BCs ---

def create_nset_from_surface(model, instance_name, surface_name, nset_name):
    """
    Create a node set in the assembly from the nodes belonging to a named surface
    on a given instance. Must be called after meshing.
    """
    assembly = model.rootAssembly
    instance = assembly.instances[instance_name]
    surface = instance.surfaces[surface_name]
    nodes_on_surface = set()
    for face in surface.faces:
        for elem in face.getElements():
            for node in elem.getNodes():
                nodes_on_surface.add(node)
    if not nodes_on_surface:
        raise RuntimeError(
            "No nodes found for surface '{}' in instance '{}'".format(surface_name, instance_name)
        )
    assembly.Set(name=nset_name, nodes=list(nodes_on_surface))
    print("Created NSET '{}' from surface '{}' on instance '{}'".format(nset_name, surface_name, instance_name))









