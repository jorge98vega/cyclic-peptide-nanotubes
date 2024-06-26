### IMPORTS ###


from mdtools.core import *


### ANALYSIS ###


def get_indices(traj, WATs, IONs, CAs, N_rings, layer=0, boundary=None,
                delta=0.1, delta_r=None, delta_z=None, offset=None,
                preselected=False, save=True, savefileWATs="iterWATs", savefileIONs="iterIONs", first=None, last=None):
    
    # layer y boundary son el número de anillos que se excluyen de sus respectivas zonas:
    #               si es 0, se selecciona todo el nanotubo
    #               si es n, se selecciona el nanotubo menos los n primeros y los n últimos anillos
    
    # CAs son los carbonos alfa de interés:
    # tiene que ser CAs del tubej si es un tubo
    #               CAs del canal si es el canal
    #               todos los CAs si es todo el bundle
    
    if boundary is None: boundary = layer
    if delta_r is None: delta_r = delta
    if delta_z is None: delta_z = delta
    if offset is None: offset = np.array([0.0, 0.0, 0.0])
    
    if first is None: first = 0
    if last is None: last = len(traj)
    
    iterWATs = []
    iterIONs = []
    if layer != boundary:
        iterWATs_b = []
        iterIONs_b = []
    
    atoms_top = get_indices_in_layer(CAs, layer)
    atoms_bot = get_indices_in_layer(CAs, N_rings-layer-1)
    if layer != boundary:
        atoms_top_b = get_indices_in_layer(CAs, boundary)
        atoms_bot_b = get_indices_in_layer(CAs, N_rings-boundary-1)
    
    if preselected:
        auxWATs = WATs
        auxIONs = IONs
    
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]
        
        if preselected:
            WATs = auxWATs[step]
            IONs = auxIONs[step]
        
        # Centro de la región
        centertop = np.sum(frame[atoms_top], axis=0)/atoms_top.size
        centerbot = np.sum(frame[atoms_bot], axis=0)/atoms_bot.size
        center = (centertop + centerbot)/2
        # Radio de la región
        rtop = np.max(distance_matrix(frame[atoms_top], frame[atoms_top]))
        rbot = np.max(distance_matrix(frame[atoms_bot], frame[atoms_bot]))
        r = max(rtop, rbot)/2 + delta_r
        # Alturas máxima y mínima de la región
        zmax = np.sum(frame[atoms_top][:,2])/atoms_top.size - center[2] + delta_z
        zmin = np.sum(frame[atoms_bot][:,2])/atoms_bot.size - center[2] - delta_z
        if layer != boundary:
            zmax_b = np.sum(frame[atoms_top_b][:,2])/atoms_top_b.size - center[2] + delta_z
            zmin_b = np.sum(frame[atoms_bot_b][:,2])/atoms_bot_b.size - center[2] - delta_z
        
        # Aguas (solo los oxígenos) en la región
        aux = []
        aux_b = []
        for atom in WATs:
            xyz = frame[atom] - (center + offset)
            if (zmin < xyz[2]) and (xyz[2] < zmax) and (xyz[0]**2+xyz[1]**2 < r**2):
                aux.append(atom)
            elif layer != boundary:
                if (zmin_b < xyz[2]) and (xyz[2] < zmax_b) and (xyz[0]**2+xyz[1]**2 < r**2):
                    aux_b.append(atom)
                
        aux = np.array(aux)
        iterWATs.append(aux)
        if layer != boundary:
            aux_b = np.array(aux_b)
            iterWATs_b.append(aux_b)
        
        # Iones en la región
        aux = []
        aux_b = []
        for atom in IONs:
            xyz = frame[atom] - (center + offset)
            if (zmin < xyz[2]) and (xyz[2] < zmax) and (xyz[0]**2+xyz[1]**2 < r**2):
                aux.append(atom)
            elif layer != boundary:
                if (zmin_b < xyz[2]) and (xyz[2] < zmax_b) and (xyz[0]**2+xyz[1]**2 < r**2):
                    aux_b.append(atom)
                
        aux = np.array(aux)
        iterIONs.append(aux)
        if layer != boundary:
            aux_b = np.array(aux_b)
            iterIONs_b.append(aux_b)
    
    iterWATs = np.array(iterWATs, dtype=object)
    iterIONs = np.array(iterIONs, dtype=object)
    if layer != boundary:
        iterWATs_b = np.array(iterWATs_b, dtype=object)
        iterIONs_b = np.array(iterIONs_b, dtype=object)
    
    if save:
        np.save(savefileWATs+".npy", iterWATs)
        np.save(savefileIONs+".npy", iterIONs)
        if layer != boundary:
            np.save(savefileWATs+"_b.npy", iterWATs_b)
            np.save(savefileIONs+"_b.npy", iterIONs_b) 
#end


def get_indices_xtal(traj, WATs, IONs, CAs, N_rings, delta_r=0.0, offsets=None, # En unidades de los lattice vectors
                     save=True, savefileWATs="iterWATs", savefileIONs="iterIONs", first=None, last=None):

    # CAs son los carbonos alfa de interés:
    # tiene que ser CAs_tubej si es un tubo
    #               CAs_canal si es el canal
    
    if offsets is None: offsets = [np.array([0.0, 0.0, 0.0])]
    
    if first is None: first = 0
    if last is None: last = len(traj)
    
    iterWATs = []
    iterIONs = []
    
    layer = 0
    atoms_top = get_indices_in_layer(CAs, layer)
    atoms_bot = get_indices_in_layer(CAs, N_rings-layer-1)
    
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]
        lvs = traj.slice(0, copy=False).unitcell_lengths[0]
        
        # Centro de la región
        centertop = np.sum(frame[atoms_top], axis=0)/atoms_top.size
        centerbot = np.sum(frame[atoms_bot], axis=0)/atoms_bot.size
        center = (centertop + centerbot)/2
        # Radio de la región
        rtop = np.max(distance_matrix(frame[atoms_top], frame[atoms_top]))
        rbot = np.max(distance_matrix(frame[atoms_bot], frame[atoms_bot]))
        r = max(rtop, rbot)/2 + delta_r
        
        # Aguas (solo los oxígenos) en la región
        aux = []
        for atom in WATs:
            for offset in offsets:
                xyz = wrap_coordinates(frame[atom], lvs) - (center + offset*lvs)
                if (xyz[0]**2+xyz[1]**2 < r**2):
                    aux.append(atom)
                    break
        aux = np.array(aux)
        iterWATs.append(aux)
        
        # Iones en la región
        aux = []
        for atom in IONs:
            for offset in offsets:
                xyz = wrap_coordinates(frame[atom], lvs) - (center + offset*lvs)
                if (xyz[0]**2+xyz[1]**2 < r**2):
                    aux.append(atom)
                    break
        aux = np.array(aux)
        iterIONs.append(aux)
    
    iterWATs = np.array(iterWATs, dtype=object)
    iterIONs = np.array(iterIONs, dtype=object)
    
    if save:
        np.save(savefileWATs+".npy", iterWATs)
        np.save(savefileIONs+".npy", iterIONs)
#end


def analyse(p, traj, label, reslist=[], layer=0, boundary=None,
            distance_cutoff=2.5, angle_cutoff=120, first=None, last=None, xtal=False):
    
    if boundary is None: boundary = layer
    
    if first is None: first = 0
    if last is None: last = len(traj)
    
    iterWATs = np.load("iterWATs_"+label+".npy", allow_pickle=True)
    iterIONs = np.load("iterIONs_"+label+".npy", allow_pickle=True)
    bondable_atoms = get_atoms_in_reslist(p.bondable, reslist)
    bondable = get_indices_between_layers(bondable_atoms, layer, p.N_rings-layer-1)
    backbone = get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), layer, p.N_rings-layer-1)
    if layer != boundary:
        iterWATs_b = np.load("iterWATs_"+label+"_b.npy", allow_pickle=True)
        iterIONs_b = np.load("iterIONs_"+label+"_b.npy", allow_pickle=True)
        bondable_b = get_indices_between_layers(bondable_atoms, boundary, layer-1)
        bondable_b = np.concatenate((bondable_b, get_indices_between_layers(bondable_atoms, p.N_rings-layer, p.N_rings-boundary-1)))
        backbone_b = get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), boundary, layer-1)
        backbone_b = np.concatenate((backbone_b, get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), p.N_rings-layer, p.N_rings-boundary-1)))
    else:
        bondable_b = np.array([], dtype=int)
        backbone_b = np.array([], dtype=int)
    
    # Base de datos de las estadísticas como una lista de diccionarios
    # | Step | Número de aguas | Número de iones | Número de puentes | Distancia media puentes |
    stats_dicts = []
    
    # Base de datos de los puentes de hidrógeno como una lista de diccionarios - complementario al grafo (abajo)
    # | Step | Donor | Hydrogen | Acceptor | Distance | Angle |
    hbonds_dicts = []
    
    # Grafo los puentes de H
    hbonds_G = nx.MultiDiGraph()
    
    for step in range(first, last):
        frame = traj.slice(step, copy=False)
        
        WATs = iterWATs[step]
        IONs = iterIONs[step]
        if layer != boundary:
            WATs_b = iterWATs_b[step]
            IONs_b = iterIONs_b[step]
        else:
            WATs_b = np.array([], dtype=int)
            IONs_b = np.array([], dtype=int)
        b = np.concatenate((WATs_b, IONs_b, bondable_b, backbone_b))
        
        N_hbonds = 0
        d_ave = 0.0
        
        # Buscamos los puentes de H del frame
        
        interesting_atoms = np.concatenate((WATs, IONs, bondable, backbone, b))
        triplets, distances, angles, presence = md.baker_hubbard(frame, periodic=xtal,
                                                         interesting_atoms=interesting_atoms, return_geometry=True,
                                                         distance_cutoff=0.1*distance_cutoff, angle_cutoff=angle_cutoff)
        
        # Evitar el conteo doble
        
        ignore_indices = []
        u, c = np.unique(triplets[presence[0]][:, 1], return_counts=True) 
        for duplicate in u[c > 1]:
            indices, = np.where(triplets[presence[0]][:, 1] == duplicate) # índices en "triplets[presence[0]][:,1]", "distances[0]"
            dmin_index = np.argmin(distances[0][presence[0]][indices]) # índice en "indices"
            ignore_indices += [index for index in np.delete(indices, dmin_index)] # índices en "triplets[presence[0]][:,1]", "distances[0]"
            
        # Guardamos los hbonds
        
        for index, ((donor, h, acceptor), d, theta) in enumerate(zip(triplets[presence[0]], distances[0][presence[0]], angles[0][presence[0]])):
            if index in ignore_indices:
                continue
            if donor in b and acceptor in b:
                continue
            if donor in backbone and acceptor in backbone:
                continue
            mydonor = MyAtom(traj.top, p.N_rings, p.N_res, donor)
            myacceptor = MyAtom(traj.top, p.N_rings, p.N_res, acceptor)
            hbonds_G.add_edge(donor, acceptor, step=step, h=h, d=10.0*d)
            hbonds_dicts.append({'step': step, 'donor': mydonor, 'h': h, 'acceptor': myacceptor, 'd': 10.0*d, 'theta': theta*180.0/np.pi})
            N_hbonds += 1
            d_ave += d
            
        # Guardamos las estadísticas
        
        if N_hbonds != 0: d_ave = d_ave/N_hbonds
        stats_dicts.append({'step': step, 'N_WATs': len(WATs), 'N_IONs': len(IONs), 'N_HBonds': N_hbonds, 'ave_dist': 10.0*d_ave})
    
    # Guardamos la información
    
    pickle.dump(hbonds_G, open(label+'_hbondsG.dat', 'wb'))
    hbonds_df = pd.DataFrame(hbonds_dicts)
    hbonds_df.to_csv(label+"_hbonds.csv")
    stats_df = pd.DataFrame(stats_dicts)
    stats_df.to_csv(label+"_stats.csv")
#end


def detail_hbonds(label):
    hbonds_df = pd.read_csv(label+"_hbonds.csv")
    Nsteps = hbonds_df['step'].max()+1
    
    # Base de datos de los puentes de H del canal como una lista de diccionarios
    # | Step | Donor | Acceptor | Número de puentes | Distancia media |
    detail_dicts = []
    
    for step in range(Nsteps):
        aux_df = hbonds_df[hbonds_df["step"] == step]
        atoms = []
        nhbonds = []
        dists = []
        for index, hbond in aux_df.iterrows():
            donor = MyAtom.from_string(hbond['donor'])
            acceptor = MyAtom.from_string(hbond['acceptor'])
            atoms_dict = {'donor': donor.resname + "-" + re.sub(r'\d+', '', donor.name),
                          'acceptor': acceptor.resname + "-" + re.sub(r'\d+', '', acceptor.name)}
            if atoms_dict not in atoms:
                atoms.append(atoms_dict)
                nhbonds.append(1)
                dists.append(hbond['d'])
            else:
                index = atoms.index(atoms_dict)
                nhbonds[index] += 1
                dists[index] += hbond['d']
        for (pair, nhb, d) in zip(atoms, nhbonds, dists):
            aux_dict = {'step': step, 'donor': pair['donor'], 'acceptor': pair['acceptor'],
                        'N_HBonds': nhb, 'd': d/nhb}
            detail_dicts.append(aux_dict)
                
    
    detail_df = pd.DataFrame(detail_dicts)
    detail_df.to_csv(label+"_detail.csv")
#end


def search_longestpaths(traj, label, xtal=False, first=None, last=None, update=1000):

    def wrap(dz, lvsz):
        wrapped_dz = ((dz + lvsz/2) % lvsz) - lvsz/2
        return wrapped_dz

    hbondsG = pickle.load(open(label + '_hbondsG.dat', 'rb'))
    if first is None: first = 0
    if last is None: last = len(traj)
    start = time.time()

    cluster_dicts = []
    path_dicts = []
    for step in range(first, last):
        if step%update == 0:
            stop = time.time()
            print(step, stop-start, "s")
            start = stop

        frame = traj.slice(step, copy=False).xyz[0]
        if xtal: lvs = traj.slice(0, copy=False).unitcell_lengths[0] # nm
        auxG = nx.MultiDiGraph(((u,v,d) for u,v,d in hbondsG.edges(data=True) if d['step'] == step))
        largest_cluster = {'step': step, 'nodes': [], 'residues': [], 'size': 0.0, 'ratio': 0.0, 'nratio': 0.0, 'percolating': 0}
        longest_path = {'step': step, 'path': [], 'residues': [], 'dz': 0.0, 'ratio': 0.0}

        # Paths
        paths = dict(nx.all_pairs_shortest_path(auxG))
        for node1 in paths:
            # Clusters
            cluster_size = len(paths[node1])
            if cluster_size > largest_cluster['size']:
                largest_cluster['nodes'] = list(paths[node1].keys())
                largest_cluster['size'] = cluster_size
            for node2 in paths[node1]:
                path = paths[node1][node2]
                if xtal:
                    totaldz = 0.0
                    for i in range(len(path)-1):
                        dz = 10.0*(frame[path[i+1]][2] - frame[path[i]][2]) # Å
                        if abs(dz) > 10.0*lvs[2]/2: dz = wrap(dz, 10*lvs[2])
                        totaldz += dz
                    dz = totaldz
                else:
                    dz = 10.0*(frame[node2][2] - frame[node1][2])
                if abs(dz) > abs(longest_path['dz']):
                    longest_path['path'] = path
                    longest_path['dz'] = dz

        # Cycles
        if xtal:
            cycles = sorted(nx.simple_cycles(auxG))
            for cycle in cycles:
                cycle.append(cycle[0])
                totaldz = 0.0
                for i in range(len(cycle)-1):
                    dz = 10.0*(frame[cycle[i+1]][2] - frame[cycle[i]][2]) # Å
                    if abs(dz) > 10.0*lvs[2]/2: dz = wrap(dz, 10*lvs[2])
                    totaldz += dz
                dz = totaldz
                if abs(dz) > abs(longest_path['dz']):
                    longest_path['path'] = cycle
                    longest_path['dz'] = dz
                    if abs(dz) >= 10*lvs[2]:
                        # stop after finding the first "percolating" cycle
                        largest_cluster['percolating'] = 1
                        break

        largest_cluster['ratio'] = largest_cluster['size']/auxG.number_of_nodes()
        source = largest_cluster['nodes'][0]
        reachable_nodes = len([n for n in list(auxG.nodes) if traj.top.atom(n).residue.name != 'LYS']) + int(traj.top.atom(source).residue.name == 'LYS')
        largest_cluster['nratio'] = largest_cluster['size']/reachable_nodes
        largest_cluster['residues'] = [traj.top.atom(node).residue.name for node in largest_cluster['nodes']]
        cluster_dicts.append(largest_cluster)

        if xtal: longest_path['ratio'] = np.abs(longest_path['dz']/(10.0*lvs[2]))
        longest_path['residues'] = [traj.top.atom(node).residue.name for node in longest_path['path']]
        path_dicts.append(longest_path)

    cluster_df = pd.DataFrame(cluster_dicts)
    path_df = pd.DataFrame(path_dicts)
    cluster_df.to_csv(label+"_largestclusters.csv")
    path_df.to_csv(label+"_longestpaths.csv")
#end


def search_paths_res(traj, label, resnamelist, first=None, last=None):

    def search_neighbors_res(G, nodes, resnamelist, path, path_dicts):
        if len(resnamelist) == 0:
            path_dicts.append({'step': step, 'path': path})
            return
        for node in nodes:
            if traj.top.atom(node).residue.name != resnamelist[0]: continue
            aux_path = path.copy()
            aux_path.append(node)
            neighbors = G.neighbors(node)
            search_neighbors_res(G, neighbors, resnamelist[1:], aux_path, path_dicts)

    hbondsG = pickle.load(open(label + '_hbondsG.dat', 'rb'))
    if first is None: first = 0
    if last is None: last = len(traj)
    reslabel = ""
    for resname in resnamelist: reslabel += resname + "-"
    reslabel = reslabel[:-1]

    path_dicts = []
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]
        auxG = nx.MultiDiGraph(((u,v,d) for u,v,d in hbondsG.edges(data=True) if d['step'] == step))
        nodes = list(auxG.nodes)
        search_neighbors_res(auxG, nodes, resnamelist, [], path_dicts)

    path_df = pd.DataFrame(path_dicts)
    path_df.to_csv(label+"_paths_"+reslabel+".csv")
#end


def water_channel_stability(traj, regex="iterWATs_channel*.npy", width=100, model="l2", dz=2.5, method="onebyone", first=None, last=None, savefile="water_stability.csv"):
    # dz in Angstrom

    def get_filepaths_with_glob(root_path: str, file_regex: str):
        return glob.glob(os.path.join(root_path, file_regex))

    def custom_search(algo, zs, dz, method):
        order = max(max(algo.width, 2 * algo.min_size) // (2 * algo.jump), 1)
        peak_inds_shifted = argrelmax(algo.score, order=order, mode="wrap")[0]
        peak_inds_arr = np.take(algo.inds, peak_inds_shifted)
        peak_inds = [0] + list(peak_inds_arr) + [algo.n_samples]

        while True:
            avs = []
            for ipeak in range(len(peak_inds)-1):
                i = peak_inds[ipeak]
                j = peak_inds[ipeak+1]
                avs.append(zs[i:j].mean())

            davs = np.abs(np.array(avs[:-1]) - np.array(avs[1:]))
            if method == "onebyone":
                conditions = np.ones(len(peak_inds), dtype=bool)
                if len(davs) > 0 and np.min(davs) < dz: conditions[np.argmin(davs)+1] = False
            elif method == "direct":
                conditions = np.array([True] + list(davs > dz) + [True])
            else:
                print("Error: method must be 'onebyone' or 'direct'")
                return

            if all(conditions): break
            peak_inds = [peak for (peak, cond) in zip(peak_inds, conditions) if cond]
        return peak_inds[1:]

    if first is None: first = 0
    if last is None: last = len(traj)
    dz = 0.1*dz # A to nm

    files = get_filepaths_with_glob(".", regex)
    WATs_channels = []
    for fileWATs in files:
        iterWATs = np.load(fileWATs, allow_pickle=True)
        WATs_channels += list(iterWATs[first]) # only waters in first frame
    WATs_channels = np.unique(np.array(WATs_channels))

    stab_dicts = []
    for atom in WATs_channels:
        zs = np.array([traj.slice(step, copy=False).xyz[0][atom][2] for step in range(first, last)])
        algo = rpt.Window(width=width, model=model).fit(zs)
        bkps = custom_search(algo, zs, dz, method) # change points
        intervals = [bkps[0]] + [bkps[i+1] - bkps[i] for i in range(len(bkps)-1)] # water stability duration
        stab_dicts.append({'index': atom, 'bkps': bkps, 'intervals': intervals})

    stab_df = pd.DataFrame(stab_dicts)
    stab_df.to_csv(savefile)
#end


### EOF ###
