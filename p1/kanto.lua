
local highways = osm2pgsql.define_way_table('osm_highway', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'linestring', projection = 3857, not_null = true }
})

local railways = osm2pgsql.define_way_table('osm_railways', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'linestring', projection = 3857, not_null = true }
})

local prefectures = osm2pgsql.define_area_table('osm_prefectures', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'multipolygon', projection = 3857, not_null = true }
})

local hot_springs = osm2pgsql.define_node_table('osm_hot_springs', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'point', projection = 3857, not_null = true }
})

local rivers = osm2pgsql.define_way_table('osm_line_rivers', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'linestring', projection = 3857, not_null = true }
})

local wards = osm2pgsql.define_area_table('osm_wards', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'multipolygon', projection = 3857, not_null = true }
})

local temples = osm2pgsql.define_node_table('osm_temples', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'point', projection = 3857, not_null = true }
})

local parks = osm2pgsql.define_area_table('osm_parks', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'multipolygon', projection = 3857, not_null = true }
})

local schools = osm2pgsql.define_node_table('osm_schools', {
    { column = 'osm_id', type = 'bigint' },
    { column = 'name', type = 'text' },
    { column = 'name_en', type = 'text' },
    { column = 'name_ja', type = 'text' },
    { column = 'geom', type = 'point', projection = 3857, not_null = true }
})

local function get_names(tags)
    local name_en = tags["name:en"]
    local name_latin = tags["name:latin"]
    local name_default = tags["name"]
    local name_ja = tags["name:ja"]

    local name = name_en or name_latin or name_default
    return name, name_en, name_ja
end


local function safe_point(object)
    local geom = object:as_point()
    if geom then return geom end
    return nil
end

local function safe_linestring(object)
    local geom = object:as_linestring()
    if geom then return geom end
    return nil
end

local function safe_multipolygon(object)
    local geom = object:as_multipolygon()
    if geom then return geom end
    return nil
end


function osm2pgsql.process_node(object)
    local name, name_en, name_ja = get_names(object.tags)
    local natural_tag = object.tags["natural"]

    local building_tag = object.tags["building"]
    local amenity_tag = object.tags["amenity"]

    local geom = safe_point(object)
 
    if natural_tag == "hot_spring" and geom then
        hot_springs:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom 
        })
    elseif building_tag == "temple" or building_tag == "shrine" or amenity_tag == "place_of_worship" then
        temples:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom 
        })
    elseif amenity_tag == "school" then
        schools:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom 
        })
    end
end

function osm2pgsql.process_relation(object)
    local name, name_en, name_ja = get_names(object.tags)

    local boundary_tag = object.tags["boundary"]
    local admin_level_tag = object.tags["admin_level"]
    local leisure_tag = object.tags["leisure"]

    local geom = safe_multipolygon(object)
    if boundary_tag == "administrative" and admin_level_tag == "4" and geom then
        prefectures:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom
        })
    elseif admin_level_tag == "8" and geom then
        wards:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom
        })
    elseif leisure_tag == "park" and geom then
        parks:insert({
            osm_id = object.id,
            name = name,
            name_en = name_en,
            name_ja = name_ja,
            geom = geom
        })
    end
end

function osm2pgsql.process_way(object)
    local name, name_en, name_ja = get_names(object.tags)

    local waterway_tag = object.tags["waterway"]
    local highway_tag = object.tags["highway"]
    local railway_tag = object.tags["railway"]

    if object.is_closed then
        local geom = safe_multipolygon(object)
        local boundary_tag = object.tags["boundary"]
        local admin_level_tag = object.tags["admin_level"]
        if boundary_tag == "administrative" and admin_level_tag == "4" and geom then
            prefectures:insert({
                osm_id = object.id,
                name = name,
                name_en = name_en,
                name_ja = name_ja,
                geom = geom
            })
        end
    end    

    if highway_tag == "motorway" or highway_tag == "motorway_link" then
        local geom = safe_linestring(object)
        if geom then
            highways    :insert({
                osm_id = object.id,
                name = name,
                name_en = name_en,
                name_ja = name_ja,
                geom = geom
            })
        end
    end

    if railway_tag == "subway" then
        local geom = safe_linestring(object)
        if geom then
            railways:insert({
                osm_id = object.id,
                name = name,
                name_en = name_en,
                name_ja = name_ja,
                geom = geom
            })
        end
    end


    if waterway_tag == "river" then
        local geom = safe_linestring(object)
        if geom then
            rivers:insert({
                osm_id = object.id,
                name = name,
                name_en = name_en,
                name_ja = name_ja,
                tags = object.tags,
                geom = geom
            })
        end    
    end
end
