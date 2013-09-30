function [ j ] = candidate_nodes(Csubstrate, node, useVirtualSwitches )
%CANDIDATE_NODES Summary of this function goes here
%   Detailed explanation goes here
    if useVirtualSwitches
        j = find(Csubstrate >=node); 
    else
        if node > 0
            j = find(Csubstrate >=node);           
        else
            j = find(Csubstrate == node);           
        end
    end
end    