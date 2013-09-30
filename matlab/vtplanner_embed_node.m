function [ mappings, phi, psi, exitflag ] = vtplanner_embed_node(n_v, phi, psi, alfa, mappings, Msubstrate, Csubstrate, Mvirtual, Cvirtual, useVirtualSwitches, silent)
%VTPLANNER_EMBED_NODE Summary of this function goes here
%   Detailed explanation goes here

    exitflag = 0;

    % mark node as visited
    psi(n_v) = 1;
     
    % list of neighbors
    neighbors = triu(Mvirtual(n_v,:));

    % max link and server capacity
    max_c = max(Csubstrate);
    max_b = max(max(Msubstrate));
        
    for m_v = 1:length(neighbors)
       
        % not a neighbor
        if neighbors(m_v) == 0
            continue
        end
        
        % already visited
        if psi(m_v) == 1
            continue
        end
        
        c_m_v = Cvirtual(m_v); % required capacity
        b_e_v = Mvirtual(n_v, m_v); % required bandwidth

        % candidate nodes, i.e. node with enough computational capacity
        theta = candidate_nodes(Csubstrate, c_m_v, useVirtualSwitches);
        theta = setdiff(theta, find(phi > 0));

        % if none is available then exit
        if isempty(theta)
            disp('no theta')
            return
        end

        % compute virtual edge strength
        min_W_S = Inf;
        min_m_s = 0;

        % randomly visit candidates
        ix = randperm(length(theta));
        theta = theta(ix);
        
        % for every candidate node m_s
        for j = 1:length(theta)

            % considere substrate path between M(n_v) -> m_s
            n_s = mappings(n_v);
            m_s = theta(j);

            % available computational capacity at substrate node m_s
            c_m_s = Csubstrate(m_s);

            %compute one path
            reverse = 1 ./ Msubstrate;
            reverse(reverse == Inf) = 0;
            [~, pred] = dijkstra_sp(sparse(reverse), n_s);
            
            % look for bottleneck link
            cur = m_s;
            prev = pred(m_s);

            min_edge = Inf;
            while prev ~= 0
                if Msubstrate(cur,prev) < min_edge
                    min_edge = Msubstrate(cur,prev);
                end
                cur = prev;
                prev = pred(prev);
            end                

            % if alfa == -1, then node must be selected randonly 
            if alfa == Inf
                if min_edge >= b_e_v
                    min_m_s = m_s;
                    break
                end
            end
            
            % bandwidth constraint not satisfied
            if min_edge < b_e_v
                continue
            end
           
            % residual bottleneck link bandwidth
            res_b = (min_edge - b_e_v) / max_b;
            
            % residual computational capacity
            res_c = (c_m_s - c_m_v) / max_c;

            % compute virtual edge strength
            if max_c == 0
                W_S = res_b;
            else
                W_S = (1 - alfa) * res_b + alfa * res_c;
            end

            % keep trak of the minimal
            if W_S <= min_W_S
                min_W_S = W_S;
                min_m_s = m_s;
            end

        end

        % if no substrate node could be found, then reject VN
        if min_m_s == 0
            disp('no min')
            return
        end

        if silent ~= 1
            disp(strcat(['Virtual machine ' num2str(m_v) ' goes to node ' num2str(m_s) ]))
        end
        
        % embed node and mark it as used
        mappings(m_v) = min_m_s; phi(min_m_s) = 1;
            
    end

    for m_v = 1:length(neighbors)
       
        % not a neighbor
        if neighbors(m_v) == 0
            continue
        end

        % already visited
        if psi(m_v) == 1
            continue
        end

        [ mappings, phi, psi, exitflag ] = vtplanner_embed_node(m_v, phi, psi, alfa, mappings, Msubstrate, Csubstrate, Mvirtual, Cvirtual, useVirtualSwitches, silent);
        
        if exitflag ~= 1
            return
        end
        
    end
    
    exitflag = 1;

end