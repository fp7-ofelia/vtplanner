function [ exitflag ] = vtplanner_standalone(in_alfa, input_virtual, input_substrate, output)
%VTPLANNER_STANDALONE_SIMULATOR_ALL Summary of this function goes here
%   Detailed explanation goes here

    % input params
    alfa = str2double(in_alfa);

    % silent
    silent = 0;

    % vSwitches
    useVirtualSwitches = 0;

    % select a substrate topology (M,C)
    load(input_virtual)

    % select a virtual topology (M,C)
    load(input_substrate)

    % sanitize input
    Msubstrate = sparse(double(Msubstrate));
    Mvirtual = sparse(double(Mvirtual));

    Csubstrate = double(Csubstrate);
    Cvirtual = double(Cvirtual);

    % random embedding
    [ mappings, exitflag ] = embed_vtplanner_capacity(Msubstrate, Csubstrate, Mvirtual, Cvirtual, useVirtualSwitches, alfa, silent);

    if exitflag ~= 1
        disp('unable to find mapping')
        return
    end

    % embed virtual links
    [ preds exitflag ~ ] = map_virtual_links(Msubstrate, Mvirtual, mappings, silent);

    if exitflag ~= 1
        disp('no capacity')
        return
    end

    % compute some metrics
    [ util_n, ~ ] = compute_node_utilization(Csubstrate, Cvirtual, mappings); % per-node utilization
    [ util_l, ~ ] = compute_link_utilization(Msubstrate, Mvirtual, preds, mappings); % per-link utilization

    % compute revenue for this virtual topology request
    revenue = compute_embedding_revenue( Mvirtual, Cvirtual, 1, 1 );
    cost = compute_embedding_cost( Mvirtual, Cvirtual, mappings, preds, 1, 1);

    disp(strcat([ 'Average node utilization: '  num2str(util_n)  ]))
    disp(strcat([ 'Average link utilization: ' num2str(util_l) ]))
    disp(strcat([ 'Embedding cost: ' num2str(cost) ]))
    disp(strcat([ 'Embedding revenue: ' num2str(revenue) ]))

    save(output,  'mappings', 'preds', 'exitflag', 'util_n', 'util_l', 'cost', 'revenue')
