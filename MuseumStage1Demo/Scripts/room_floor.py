"""The room parquet is a material on one slab, shared by repair and regeneration."""
import unreal
from pathlib import Path

def ensure_room_floor():
    path='/Game/Stage1/Materials/M_room_floor'
    mat=unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_room_floor','/Game/Stage1/Materials',unreal.Material,unreal.MaterialFactoryNew())
    mat.set_editor_property('used_with_instanced_static_meshes',True)
    unreal.MaterialEditingLibrary.delete_all_material_expressions(mat)
    position=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionWorldPosition,-650,0)
    pattern=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionCustom,-400,0)
    pin=unreal.CustomInput();pin.set_editor_property('input_name','WorldPos')
    pattern.set_editor_properties({'inputs':[pin],'output_type':unreal.CustomMaterialOutputType.CMOT_FLOAT4,
        'code':(Path(__file__).parent/'room_floor.hlsl').read_text(encoding='utf8')})
    assert unreal.MaterialEditingLibrary.connect_material_expressions(position,'',pattern,'WorldPos')
    for prop,channels,y in [(unreal.MaterialProperty.MP_BASE_COLOR,(True,True,True,False),0),
                            (unreal.MaterialProperty.MP_ROUGHNESS,(False,False,False,True),180)]:
        mask=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionComponentMask,-100,y)
        mask.set_editor_properties(dict(zip(('r','g','b','a'),channels)))
        assert unreal.MaterialEditingLibrary.connect_material_expressions(pattern,'',mask,'')
        assert unreal.MaterialEditingLibrary.connect_material_property(mask,'',prop)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    assert unreal.EditorAssetLibrary.save_loaded_asset(mat,only_if_is_dirty=False)
    return mat
