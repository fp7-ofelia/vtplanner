function [ rnd ] = pick_random_entry( array )
%PICK_RANDOM_ENTRY Summary of this function goes here
%   Detailed explanation goes here
    idx = randi(length(array));
    rnd = array(idx);
end


