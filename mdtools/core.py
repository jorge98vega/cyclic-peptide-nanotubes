### IMPORTS ###


import math
import time
import numpy as np
import pandas as pd
import networkx as nx
from scipy.spatial import distance_matrix
from scipy.spatial.distance import pdist
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as clr
import matplotlib.path as mpath
import matplotlib.collections as mcoll
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import axes3d
import pytraj as pt
import mdtraj as md


### MAIN ###


def orient(p, p0, pZ, pX):
    '''
    Cambia las coordenadas de "punto" a un nuevo sistema de referencia en el que "p0" es el 0,
    el eje Z está orientado de "p0" a "pZ", y el eje X está orientado de "p0" al punto "pX" proyectado
    sobre el plano perpendicular al nuevo eje Z
    '''
    
    vZ = pZ - p0 # Vector from p0 to pZ
    uZ = vZ/np.linalg.norm(vZ) # Vector del nuevo eje Z
    
    if pX is None:
        uX = np.array([1.0, 0.0, 0.0])
    else:
        wX = pX - p0 # Vector de p0 a pX
        vX = wX - np.dot(wX, uZ)*uZ # wX proyectado sobre el plano perpendicular a uZ
        uX = vX/np.linalg.norm(vX) # Vector del nuevo eje X
    
    uY = np.cross(uZ, uX) # Vector del nuevo eje Y
    
    vp = p - p0 # Vector de p0 a punto
    orientado = np.array([np.dot(vp, uX), np.dot(vp, uY), np.dot(vp, uZ)])
    return orientado
#end


def recenter_traj_RMSD(run_name, N_tubes, N_res):
    '''
    Vamos a tomar:
    como p0 el centro de masa de los carbonos alfas de los 4 tubos
    como pZ el centro de masa de los carbonos alfas de los primeros anillos de los nanotubos
    como pX el centro de masa de los carbonos alfas del tubo 1
    '''
    traj = md.load(run_name+"_MD.nc", top=run_name+".parm7")
    
    CAs = traj.top.select("name==CA")
    CAs_tube1 = CAs[0:int(CAs.size/N_tubes)]
    CAs_tube2 = CAs[int(CAs.size/N_tubes):int(2*CAs.size/N_tubes)]
    CAs_tube3 = CAs[int(2*CAs.size/N_tubes):int(3*CAs.size/N_tubes)]
    CAs_tube4 = CAs[int(3*CAs.size/N_tubes):int(4*CAs.size/N_tubes)]
    CAs_top = np.concatenate((CAs_tube1[0:N_res], CAs_tube2[0:N_res], CAs_tube3[0:N_res], CAs_tube4[0:N_res]))
    CAs_bot = np.concatenate((CAs_tube1[-N_res:], CAs_tube2[-N_res:], CAs_tube3[-N_res:], CAs_tube4[-N_res:]))
    
    step = len(traj)-1
    p0 = np.sum(traj.xyz[step][CAs], axis=0)/CAs.size
    pZ = np.sum(traj.xyz[step][CAs_top], axis=0)/CAs_top.size
    pX = np.sum(traj.xyz[step][CAs_tube1], axis=0)/CAs_tube1.size
    
    selection = CAs
    xyz = []
    for atom in selection:
        xyz.append(orient(traj.xyz[step][atom], p0, pZ, pX))

    oriented = md.Trajectory(xyz, traj.top.subset(selection))
    
    traj.superpose(oriented, 0, atom_indices=selection, ref_atom_indices=range(oriented.n_atoms))
    traj.save(run_name+"_RMSD.nc")
#end


class MyAtom:
    def __init__(self, index, name, residue, resname, tube=None, layer=None):
        self.index = index
        self.name = name
        self.residue = residue
        self.resname = resname
        self.tube = tube
        self.layer = layer
    
    def __str__(self): # print()
        return "MyAtom(index=" + str(self.index) + ", name=" + str(self.name) + ", residue=" + str(self.residue) + ", resname=" + str(self.resname) + ", tube=" + str(self.tube) + ", layer=" + str(self.layer) + ")"
    
    def __repr__(self):
        return "MyAtom(index=" + str(self.index) + ", name=" + str(self.name) + ", residue=" + str(self.residue) + ", resname=" + str(self.resname) + ", tube=" + str(self.tube) + ", layer=" + str(self.layer) + ")"
#end


class MyAtomSelection:
    def __init__(self, name, resname, selection=None):
        self.name = name
        self.resname = resname
        if selection is None: self.selection = "name " + name + " and resname " + resname
        else: self.selection = selection
        
    def __str__(self): # print()
        return "MyAtomSelection(name=" + str(self.name) + ", resname=" + str(self.resname) + ", selection=" + str(self.selection) + ")"
    
    def __repr__(self):
        return "MyAtomSelection(name=" + str(self.name) + ", resname=" + str(self.resname) + ", selection=" + str(self.selection) + ")"
#end


def select_atoms(traj, N_rings, N_res, myselection):
    return np.array([
        MyAtom(atom.index, myselection.name, atom.residue.index, myselection.resname,
               atom.residue.index//(N_rings*N_res), (atom.residue.index//N_res)%N_rings)
        for atom in [traj.top.atom(index) for index in traj.top.select(myselection.selection)]
    ])
#end


class MyParams:
    def __init__(self, traj, N_tubes, N_rings, N_res, myselections):
        
        self.N_tubes = N_tubes
        self.N_rings = N_rings
        self.N_res = N_res
        N_allres = N_tubes*N_rings*N_res
        self.N_allres = N_allres

        self.CAs = select_atoms(traj, N_rings, N_res, MyAtomSelection("CA", None, "name CA"))
        self.bbNs = select_atoms(traj, N_rings, N_res, MyAtomSelection("bbN", None, "name N and resid 1 to " + str(N_allres)))
        self.bbOs = select_atoms(traj, N_rings, N_res, MyAtomSelection("bbO", None, "name O and resid 1 to " + str(N_allres)))
        
        others = np.array([], dtype=object)
        for myselection in myselections:
            others = np.concatenate((others, select_atoms(traj, N_rings, N_res, myselection)))
        self.others = others
        
        self.WATs = traj.top.select("water and name O")
        self.IONs = traj.top.select("element Cl")
#end


def get_reslist(N_rings, N_res, tube, residues):
    reslist = []
    for layer in range(N_rings):
        reslist.append(tube*N_rings*N_res + layer*N_res + residues[layer%len(residues)])
    return reslist
#end


def get_channel_reslist(N_rings, N_res, tubes, tuberesidues):
    reslist = []
    for i, tube in enumerate(tubes):
        reslist.append(get_reslist(N_rings, N_res, tube, tuberesidues[i]))
    return reslist
#end


def get_atoms_in_reslist(myatoms, reslist):
    return np.array([atom for atom in myatoms if atom.residue in reslist])
#end


def get_indices_in_layer(myatoms, layer):
    return np.array([atom.index for atom in myatoms if atom.layer == layer])
#end


def wrap_coordinates(point, box):
    for dim in range(3):
        point[dim] = ((point[dim] + box[dim]/2) % box[dim]) - box[dim]/2
    
    return point
#end


def periodic_pdist(positions, box):
    dist = 0
    
    for dim in range(3):
        pddim = pdist(positions[:, dim].reshape(positions.shape[0], 1))
        pddim[pddim > 0.5*box[dim]] -= box[dim] # ? apply boundary conditions
        dist += pddim**2
        
    return np.sqrt(dist)
#end


def decorate_ax(ax, title, titlesize, xlabel, ylabel, labelsize, ticksize, linewidth, length, legend):
    ax.set_title(title, fontsize=titlesize, pad=titlesize)
    ax.set_xlabel(xlabel, fontsize=labelsize)#, labelpad=15)
    ax.set_ylabel(ylabel, fontsize=labelsize)#, labelpad=15)
    ax.tick_params(top=True, right=True, labelsize=ticksize, width=linewidth, length=length)
    for axis in ['top','bottom','left','right']:
        ax.spines[axis].set_linewidth(linewidth)
    if legend:
        ax.legend(fontsize=ticksize, edgecolor='0.75')
#end


### EOF ###