__addr  = 0x800B0000;

D_100004 = 0x100004;
D_1F800002 = 0x1F800002;
D_1F800008 = 0x1F800008;
D_1F8000D0 = 0x1F8000D0;
D_1F800288 = 0x1F800288;
D_1F8002F4 = 0x1F8002F4;
D_1F8003A8 = 0x1F8003A8;
D_800E7738 = 0x800E7738;

D_801256EC = debug_text_ot + 0x4;
D_801256F4 = debug_text_ot + 0xC;


D_80102804 = D_801027FC + 0x8;
D_8010280C = D_801027FC + 0x10;

D_8010292E = D_8010292C + 0x2;

D_80103174 = D_80103164 + 0x10;
D_80103184 = D_80103164 + 0x20;
D_80103194 = D_80103164 + 0x30;
D_801031A4 = D_80103164 + 0x40;
D_801031B4 = D_80103164 + 0x50;
D_801031C4 = D_80103164 + 0x60;
D_801031D4 = D_80103164 + 0x70;

D_8010351C = D_8010350C + 0x10;

D_801048DC = D_801048CC + 0x10;

D_8011E97A = D_8011E978 + 0x2;
D_8011E97C = D_8011E978 + 0x4;

D_8011F884 = D_8011F880 + 0x4;
D_8011F888 = D_8011F880 + 0x8;

D_8011F894 = D_8011F890 + 0x4;
D_8011F898 = D_8011F890 + 0x8;



D_801380D0 = player_entity + 0x18;
D_801380F0 = D_801380D0 + 0x20;
D_80138110 = D_801380F0 + 0x20;
D_80138120 = D_80138110 + 0x10;
D_80138124 = D_80138120 + 0x4;
D_80138128 = D_80138124 + 0x4;
D_8013812C = D_80138128 + 0x4;
D_80138130 = D_8013812C + 0x4;
D_80138134 = D_80138130 + 0x4;
D_80138138 = D_80138134 + 0x4;
D_8013813C = D_80138138 + 0x4;
D_80138140 = D_8013813C + 0x4;
D_80138144 = D_80138140 + 0x4;
D_80138148 = D_80138144 + 0x4;
D_80138150 = D_80138148 + 0x8;
D_80138154 = D_80138150 + 0x4;
D_80138158 = D_80138154 + 0x4;
D_80138164 = D_80138158 + 0xc;
D_80138168 = D_80138164 + 0x4;
D_8013816C = D_80138168 + 0x4;
D_80138176 = D_8013816C + 0xa;
D_80138184 = D_80138176 + 0xe;
D_80138188 = D_80138184 + 0x4;
D_8013818C = D_80138188 + 0x4;
D_80138194 = D_8013818C + 0x8;
D_80138198 = D_80138194 + 0x4;
D_8013819C = D_80138198 + 0x4;
D_8013819D = D_8013819C + 0x1;
D_8013819E = D_8013819D + 0x1;
D_8013819F = D_8013819E + 0x1;
D_801381A1 = D_8013819F + 0x2;
D_801381A2 = D_801381A1 + 0x1;
D_801381A4 = D_801381A2 + 0x2;
D_801381A8 = D_801381A4 + 0x4;
D_801381AC = D_801381A8 + 0x4;

D_8014144A = D_80141448 + 2;
D_8014144C = D_80141448 + 4;

/* buildfix: names the regenerated asm (tools/buildfix/regen.py) still uses */
D_801026E4 = menu_selection;
D_801026E8 = menu_is_visible;
D_801029F4 = menu_animation_timer;
D_80102780 = debug_font_x;
D_80102784 = debug_font_y;
D_80102790 = debug_ot_index;
D_8010295C = entity_list_0;
D_8010296C = entity_list_1;
D_8010297C = entity_list_2;
D_801256E8 = debug_text_ot;
D_8012B740 = debug_char_uvs;
D_80137D00 = gbuffers;
D_801380B8 = player_entity;
D_801383F8 = entity_ptrs;
D_80138628 = mesh_array;
D_8013F448 = sin_lut;
D_80142CC8 = gbuffer_current_index;
func_800D0438 = get_list1_head;
func_800D0458 = get_list2_head;
func_800D0468 = get_list2_tail;
func_800D0478 = get_list0_head;
func_800D0498 = entity_insert_before;
func_800D04B0 = entity_insert_after;
func_800D04E8 = entity_create;
func_800D053C = entity_destroy;
func_800DA46C = set_render_distance_horizontal;
func_800DA498 = set_render_distance_vertical;
func_800DA4A8 = set_simulation_distance;
func_800DAB0C = is_outside_simulation_range;
func_800DABF8 = is_outside_render_range;
func_800E0A40 = data_buffer_get_ptr;
func_800E0A50 = data_buffer_alloc;
func_800E0A78 = data_buffer_dealloc;
func_800E0AA0 = data_buffer_reset;
func_800E0AF8 = gbuffer_reset;
func_800E0F94 = gbuffer_get_current;
func_800E0FBC = gbuffer_get_next_ot;
func_800E100C = gbuffer_swap;
func_800E9788 = my_DrawSync;
func_800E97B8 = my_LoadImage;
func_800EA2F4 = ui_draw_sprite;
func_800ECD88 = objective_add;
func_800DEAD4 = GetTPage;
func_800DEB6C = GetClut;
func_800DED4C = SetSemiTrans;
func_800CBCE4 = rsin;
