function [ preds exitflag Mallocated edge_nb ] = map_virtual_links( Msubstrate, Mvirtual, mappings, silent )
%MAP_VIRTUAL_LINKS Maps virtual links on substrate topology using dijkstra.
%   Accepts the substrate topology matrix Msubstrate, the substrate
%   capacity Csubstrate, the virtual topology matrix, the virtual capacity
%   Cvirtual, and the mappings. If silent is set to 1 nothing is pronted on
%   screen

    Nvirtual = length(Mvirtual);
    Nsubstrate= length(Msubstrate);
    Mallocated = zeros(Nsubstrate, Nsubstrate);

    preds = zeros(1, Nsubstrate);
    edge_nb = 1;
    
    for i=1:Nvirtual
       
        for j = i:Nvirtual
        
            if i == j                              % ignore links to self
                continue
            end
            
            if Mvirtual(i, j) == 0                     % there is no link between the two node
                continue
            end
            
            i_t = mappings(i);                     % find mapping of node i in the substrate topolgy
            j_t = mappings(j);                     % find mapping of node j in the substrate topolgy
            
            if silent ~= 1
                disp(strcat([ 'I shall find a path to virtual node ' num2str(i) ' (' num2str(i_t) ') from virtual node ' num2str(j) ' (' num2str(j_t) ') with capacity ' num2str(Mvirtual(i,j)) ]))
            end
            
            tmp = Msubstrate - (Mallocated + Mallocated');
            tmp(tmp<Mvirtual(i,j)) = 0;

            reverse = 1 ./ tmp;
            reverse(reverse == Inf) = 0;
            [d, pred] = dijkstra_sp(sparse(reverse), i_t);

            if d(j_t) == Inf
                exitflag = -10;
                return
            end
            
            preds(edge_nb, :) = pred;
             
            path = [ ];
            
            cur = j_t;
            prev = preds(edge_nb,j_t);
            
            while prev ~= 0
                
                path = [ path ' -> ' num2str(prev) ];
                
                if silent ~= 1
                    disp(['Edge ' num2str(cur) ' -> ' num2str(prev) ])
                end
                
                Mallocated(cur, prev) = Mallocated(cur, prev) + Mvirtual(i, j);
                cur = prev;
                prev = preds(edge_nb,prev);
                
            end

            edge_nb = edge_nb + 1;

            if silent ~= 1
                disp(strcat(['Substrate path is ' num2str(j_t) path ]))
            end
            
        end
        
    end
    
    Mallocated = Mallocated + Mallocated';

    exitflag = 1;
    
end

