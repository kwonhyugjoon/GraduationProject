// One opaque surface: parquet joints and grain never overlap other floor polygons.
float2 p = float2(WorldPos.x + WorldPos.y, WorldPos.y - WorldPos.x) * .70710678;
float2 tile = floor(p / 60.0);
float2 f = frac(p / 60.0);
bool vertical = fmod(abs(tile.x + tile.y), 2.0) < 1.0;
float2 uv = vertical ? f.yx : f;
float plank = floor(uv.y * 4.0);
float2 local = float2(uv.x, frac(uv.y * 4.0));
float joint = min(min(local.x, 1.0-local.x)*60.0, min(local.y,1.0-local.y)*15.0);
float edge = smoothstep(.12,.28,joint);
float seed = frac(sin(dot(tile,float2(17.13,93.71))+plank*39.17)*43758.5453);
float grain = sin(uv.x*115.0+sin(uv.x*17.0+seed*11.0)*1.5+local.y*16.0);
float fine = sin(uv.x*430.0+seed*37.0+local.y*35.0);
float3 wood = lerp(float3(.22,.095,.035),float3(.31,.15,.065),seed);
wood *= 1.0 + grain*.055 + fine*.018;
return float4(lerp(float3(.055,.026,.012),wood,edge),lerp(.74,.54+seed*.07,edge));
