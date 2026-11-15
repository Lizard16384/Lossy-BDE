summon falling_block ~ ~.8 ~ {BlockState:{id:redstone_block},Passengers:[{id:falling_block,BlockState:{id:activator_rail}},
{id:command_block_minecart,Command:"setblock ~ ~-2 ~ repeating_command_block{auto:1,Command:'fill ~ ~ ~ ~ ~2 ~ air'}"},
$(data:summons)
{id:command_block_minecart,Command:"execute align xz run kill @e[type=command_block_minecart,dy=0]"}]}
