try:
    from imgui_bundle import imgui
    from imgui_bundle import ImVec2
    import p3dimgui
    import p3dimgui.backend as p3dimgui_backend
    import p3dimgui.shaders as p3dimgui_shaders
    HAS_P3D_IMGUI = True
except Exception:
    p3dimgui = None
    imgui = None
    ImVec2 = None
    HAS_P3D_IMGUI = False

def apply_imgui_patches():
    """Apply patches to p3dimgui backend for better mouse handling"""
    if not HAS_P3D_IMGUI:
        return False

    try:
        p3dimgui_backend.VERT_SHADER = p3dimgui_shaders.VERT_SHADER
        p3dimgui_backend.FRAG_SHADER = p3dimgui_shaders.FRAG_SHADER

        if getattr(p3dimgui_backend, "_aim_trainer_mouse_patch", False):
            return True

        def _patched_window_event(self, _=None):
            if not self.window:
                return
            win_x = max(1, int(self.window.getXSize()))
            win_y = max(1, int(self.window.getYSize()))
            fb_x = max(1, int(getattr(self.window, "getFbXSize", lambda: win_x)()))
            fb_y = max(1, int(getattr(self.window, "getFbYSize", lambda: win_y)()))
            self._aim_trainer_window_size = (win_x, win_y)
            self._aim_trainer_framebuffer_size = (fb_x, fb_y)
            self.io.display_size = (win_x, win_y)
            self.io.display_framebuffer_scale = (fb_x / win_x, fb_y / win_y)

        def _patched_new_frame(self, task):
            if self.root.isHidden():
                return task.cont

            self.io.delta_time = base.clock.getDt()
            self._ImGuiBackend__windowEvent()
            win_x, win_y = getattr(self, "_aim_trainer_window_size", (1, 1))

            if getattr(base, "mouseWatcherNode", None) and base.mouseWatcherNode.hasMouse():
                mouse_x = (base.mouseWatcherNode.getMouseX() + 1.0) * 0.5 * win_x
                mouse_y = (1.0 - ((base.mouseWatcherNode.getMouseY() + 1.0) * 0.5)) * win_y
                self.io.mouse_pos = (mouse_x, mouse_y)
            elif self.window:
                mouse = self.window.getPointer(0)
                if mouse.getInWindow():
                    self.io.mouse_pos = (mouse.getX(), mouse.getY())
                else:
                    self.io.mouse_pos = (-imgui.FLT_MAX, -imgui.FLT_MAX)
            else:
                self.io.mouse_pos = (-imgui.FLT_MAX, -imgui.FLT_MAX)

            imgui.new_frame()
            base.messenger.send("imgui-new-frame")
            return task.cont

        def _patched_render_frame(self, task):
            if self.root.isHidden():
                return task.cont

            imgui.render()
            draw_data = imgui.get_draw_data()
            clip_off = draw_data.display_pos
            clip_scale = draw_data.framebuffer_scale
            fb_width = int(draw_data.display_size.x * clip_scale.x)
            fb_height = int(draw_data.display_size.y * clip_scale.y)
            if fb_width <= 0 or fb_height <= 0:
                return task.cont

            self._ImGuiBackend__updateTextures()

            for child in self.root.children:
                child.detachNode()

            for i, cmd_list in enumerate(draw_data.cmd_lists):
                if i > len(self.geomData) - 1:
                    self.geomData.append(
                        p3dimgui_backend.GeomList(
                            p3dimgui_backend.GeomVertexData(
                                f"imgui-vertex-{i}",
                                self.vformat,
                                p3dimgui_backend.Geom.UH_stream,
                            )
                        )
                    )

                geom_list = self.geomData[i]
                vertex_handle = geom_list.vdata.modifyArrayHandle(0)
                if vertex_handle.getNumRows() < cmd_list.vtx_buffer.size():
                    vertex_handle.uncleanSetNumRows(cmd_list.vtx_buffer.size())
                vertex_handle.setData(
                    p3dimgui_backend.ctypes.string_at(
                        cmd_list.vtx_buffer.data_address(),
                        cmd_list.vtx_buffer.size() * imgui.VERTEX_SIZE,
                    )
                )

                index_buffer = cmd_list.idx_buffer.data_address()
                for k, draw_cmd in enumerate(cmd_list.cmd_buffer):
                    if k > len(geom_list.nodepaths) - 1:
                        geom_list.nodepaths.append(
                            p3dimgui_backend.ImGuiBackend._ImGuiBackend__createGeomnode(geom_list.vdata)
                        )

                    np = geom_list.nodepaths[k]
                    np.reparentTo(self.root)
                    node = np.node()

                    index_handle = node.modifyGeom(0).modifyPrimitive(0).modifyVertices(draw_cmd.elem_count).modifyHandle()
                    if index_handle.getNumRows() < draw_cmd.elem_count:
                        index_handle.uncleanSetNumRows(draw_cmd.elem_count)

                    index_handle.setData(
                        p3dimgui_backend.ctypes.string_at(
                            index_buffer,
                            draw_cmd.elem_count * imgui.INDEX_SIZE,
                        )
                    )
                    index_buffer += draw_cmd.elem_count * imgui.INDEX_SIZE

                    state = p3dimgui_backend.RenderState.makeEmpty()

                    if draw_cmd.tex_ref.get_tex_id():
                        texture = self.textures[draw_cmd.tex_ref.get_tex_id()]
                        state = state.addAttrib(p3dimgui_backend.TextureAttrib.make(texture))

                    node.setGeomState(0, state)

            return task.cont

        p3dimgui_backend.ImGuiBackend._ImGuiBackend__windowEvent = _patched_window_event
        p3dimgui_backend.ImGuiBackend._ImGuiBackend__newFrame = _patched_new_frame
        p3dimgui_backend.ImGuiBackend._ImGuiBackend__renderFrame = _patched_render_frame
        p3dimgui_backend._aim_trainer_mouse_patch = True

        return True
    except Exception as e:
        print(f"Failed to apply imgui patches: {e}")
        return False
