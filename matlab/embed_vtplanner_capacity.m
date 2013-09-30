function [ mappings, exitflag ] = embed_vtplanner_capacity(Msubstrate, Csubstrate, Mvirtual, Cvirtual, useVirtualSwitches, params, silent)
%EMBED_VTPLANNER. Embed a virtual topology request using the vtplanner algorithm.
% Embed a virtual topology request using the vtplanner algorithm. The virtual
% topology and the substrate topology are described only by they
% computational capacity vectors. If useVirtualSwitches is set to 1, the 
% embedding algorithm will use also the virtual switches; if it is set to 0
% virtual switches will not be used. Notice hat this means that switches 
% are mapped to node with computational capacity > 0 and not only to node 
% whose computational capacity is set to 0 (which indicate switches). If 
% silent is set to 1 nothing is printed to screen.

    exitflag = 0;

    alfa = params(1);

    Ns = length(Msubstrate); % number of substrate nodes
    Nv = length(Mvirtual); % number of virtual nodes
    
    mappings = zeros(1, Nv); % set of mappings
    psi = zeros(1, Nv); % visited nodes
    phi = zeros(1, Ns); % used nodes

    % pick node with highest outgoing capacity
    capacity_v = sum(Mvirtual);
    max_capacity_v = max(capacity_v);
    highest_v = find(capacity_v == max_capacity_v);

    % pick one of the candidate node randomly
    n_v = pick_random_entry(highest_v);
    
    % mark node as visited
    psi(n_v) = 1;
    
    % candidate nodes, i.e. node with enough computational capacity
    nodes = candidate_nodes(Csubstrate, Cvirtual(n_v), useVirtualSwitches);
    
    if isempty(nodes)
        return
    end
    
    % pick node with highest outgoing capacity
    removed = setdiff(1:Ns, nodes);
    Msubstrate(:, removed) = 0;
    capacity_s = sum(Msubstrate);
    max_capacity_s = max(capacity_s);
    highest_s = find(capacity_s == max_capacity_s);
    
    % pick one of the candidate node randomly
    n_s = pick_random_entry(highest_s);

    if silent ~= 1
        disp(strcat(['Virtual node ' num2str(n_v) ' goes to node ' num2str(n_s) ]))
    end    
    
    mappings(n_v) = n_s; phi(n_s) = 1; % embed and mark as used
    
    [ mappings, ~, ~, exitflag ] = vtplanner_embed_node(n_v, phi, psi, alfa, mappings, Msubstrate, Csubstrate, Mvirtual, Cvirtual, useVirtualSwitches, silent);
   
end
