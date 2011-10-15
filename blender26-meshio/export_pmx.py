# coding: utf-8

import io
from . import bl
from . import oneskinmesh
from .pymeshio import pmx
from .pymeshio import common
from .pymeshio.pmx import writer


def create_pmx(ex):
    model=pmx.Model()
    model.name=ex.name
    model.comment=ex.comment

    def get_deform(b0, b1, weight):
        print(b0, b1, weight)
        if b0==-1:
            return pmx.Bdef1(b1, weight)
        elif b1==-1:
            return pmx.Bdef1(b0, weight)
        else:
            return pmx.Bdef2(b0, b1, weight)

    model.vertices=[pmx.Vertex(
        # convert right-handed z-up to left-handed y-up
        common.Vector3(pos[0], pos[2], pos[1]), 
        # convert right-handed z-up to left-handed y-up
        common.Vector3(attribute.nx, attribute.nz, attribute.ny),
        # reverse vertical
        common.Vector2(attribute.u, 1.0-attribute.v),
        get_deform(ex.skeleton.indexByName(b0), ex.skeleton.indexByName(b1), weight),
        # edge flag, 0: enable edge, 1: not edge
        1.0 
        )
        for pos, attribute, b0, b1, weight in ex.oneSkinMesh.vertexArray.zip()]

    # bones
    boneNameMap={}
    for i, b in enumerate(self.skeleton.bones):

        # name
        boneNameMap[b.name]=i
        v=englishmap.getUnicodeBoneName(b.name)
        if not v:
            v=[b.name, b.name]
        assert(v)
        bone=pmx.Bone(v[1])
        bone.english_name=b.name

        if len(v)>=3:
            # has type
            if v[2]==5:
                b.ik_index=self.skeleton.indexByName('eyes')
            bone.type=v[2]
        else:
            bone.type=b.type

        bone.parent_index=b.parent_index
        bone.tail_index=b.tail_index
        bone.ik_index=b.ik_index

        # convert right-handed z-up to left-handed y-up
        bone.pos.x=b.pos[0] if not near(b.pos[0], 0) else 0
        bone.pos.y=b.pos[2] if not near(b.pos[2], 0) else 0
        bone.pos.z=b.pos[1] if not near(b.pos[1], 0) else 0
        
        model.bones.append(bone)
    return model

    # IK
    for ik in self.skeleton.ik_list:
        solver=pmd.IK()
        solver.index=self.skeleton.getIndex(ik.target)
        solver.target=self.skeleton.getIndex(ik.effector)
        solver.length=ik.length
        b=self.skeleton.bones[ik.effector.parent_index]
        for i in range(solver.length):
            solver.children.append(self.skeleton.getIndex(b))
            b=self.skeleton.bones[b.parent_index]
        solver.iterations=ik.iterations
        solver.weight=ik.weight
        model.ik_list.append(solver)

    # 面とマテリアル
    vertexCount=self.oneSkinMesh.getVertexCount()
    for material_name, indices in self.oneSkinMesh.vertexArray.each():
        #print('material:', material_name)
        try:
            m=bl.material.get(material_name)
        except KeyError as e:
            m=DefaultMatrial()
        def get_texture_name(texture):
            pos=texture.replace("\\", "/").rfind("/")
            if pos==-1:
                return texture
            else:
                return texture[pos+1:]
        textures=[get_texture_name(path)
            for path in bl.material.eachEnalbeTexturePath(m)]
        print(textures)
        # マテリアル
        model.materials.append(pmd.Material(
                # diffuse_color
                common.RGB(m.diffuse_color[0], m.diffuse_color[1], m.diffuse_color[2]),
                m.alpha,
                # specular_factor
                0 if m.specular_toon_size<1e-5 else m.specular_hardness*10,
                # specular_color
                common.RGB(m.specular_color[0], m.specular_color[1], m.specular_color[2]),
                # ambient_color
                common.RGB(m.mirror_color[0], m.mirror_color[1], m.mirror_color[2]),
                # flag
                1 if m.subsurface_scattering.use else 0,
                # toon
                0,
                # vertex_count
                len(indices),
                # texture
                ('*'.join(textures) if len(textures)>0 else "").encode('cp932')
                ))
        # 面
        for i in indices:
            assert(i<vertexCount)
        for i in range(0, len(indices), 3):
            # reverse triangle
            model.indices.append(indices[i])
            model.indices.append(indices[i+1])
            model.indices.append(indices[i+2])

    # 表情
    for i, m in enumerate(self.oneSkinMesh.morphList):
        v=englishmap.getUnicodeSkinName(m.name)
        if not v:
            v=[m.name, m.name, 0]
        assert(v)
        # morph
        morph=pmd.Morph(v[1].encode("cp932"))
        morph.english_name=m.name.encode("cp932")
        m.type=v[2]
        morph.type=v[2]
        for index, offset in m.offsets:
            # convert right-handed z-up to left-handed y-up
            morph.append(index, offset[0], offset[2], offset[1])
        morph.vertex_count=len(m.offsets)

    # 表情枠
    # type==0はbase
    for i, m in enumerate(self.oneSkinMesh.morphList):
        if m.type==3:
            model.morph_indices.append(i)
    for i, m in enumerate(self.oneSkinMesh.morphList):
        if m.type==2:
            model.morph_indices.append(i)
    for i, m in enumerate(self.oneSkinMesh.morphList):
        if m.type==1:
            model.morph_indices.append(i)
    for i, m in enumerate(self.oneSkinMesh.morphList):
        if m.type==4:
            model.morph_indices.append(i)

    # ボーングループ
    for g in self.skeleton.bone_groups:
        name=englishmap.getUnicodeBoneGroupName(g[0])
        if not name:
            name=g[0]
        englishName=g[0]

        model.bone_group_list.append(pmd.BoneGroup(
                (name+'\n').encode('cp932'),
                (englishName+'\n').encode('cp932')
                ))

    # ボーングループメンバー
    for i, b in enumerate(self.skeleton.bones):
        if i==0:
           continue
        if b.type in [6, 7]:
           continue
        model.bone_display_list.append((i, self.skeleton.getBoneGroup(b)))

    # English
    model.english_name=self.englishName.encode('cp932')
    model.english_comment=self.englishComment.encode('cp932')

    # toon
    toonMeshObject=None
    for o in bl.object.each():
        try:
            if o.name.startswith(bl.TOON_TEXTURE_OBJECT):
                toonMeshObject=o
        except:
            p(o.name)
        break
    if toonMeshObject:
        toonMesh=bl.object.getData(toonMeshObject)
        toonMaterial=bl.mesh.getMaterial(toonMesh, 0)
        for i in range(10):
            t=bl.material.getTexture(toonMaterial, i)
            if t:
                model.toon_textures[i]=("%s" % t.name).encode('cp932')
            else:
                model.toon_textures[i]=("toon%02d.bmp" % (i+1)).encode('cp932')
    else:
        for i in range(10):
            model.toon_textures[i]=("toon%02d.bmp" % (i+1)).encode('cp932')

    # rigid body
    rigidNameMap={}
    for i, obj in enumerate(self.oneSkinMesh.rigidbodies):
        name=obj[bl.RIGID_NAME] if bl.RIGID_NAME in obj else obj.name
        print(name)
        rigidNameMap[name]=i
        boneIndex=boneNameMap[obj[bl.RIGID_BONE_NAME]]
        if boneIndex==0:
            boneIndex=-1
            bone=self.skeleton.bones[0]
        else:
            bone=self.skeleton.bones[boneIndex]
        if obj[bl.RIGID_SHAPE_TYPE]==0:
            shape_type=pmd.SHAPE_SPHERE
            shape_size=common.Vector3(obj.scale[0], 0, 0)
        elif obj[bl.RIGID_SHAPE_TYPE]==1:
            shape_type=pmd.SHAPE_BOX
            shape_size=common.Vector3(obj.scale[0], obj.scale[1], obj.scale[2])
        elif obj[bl.RIGID_SHAPE_TYPE]==2:
            shape_type=pmd.SHAPE_CAPSULE
            shape_size=common.Vector3(obj.scale[0], obj.scale[2], 0)
        rigidBody=pmd.RigidBody(
                name.encode('cp932'), 
                collision_group=obj[bl.RIGID_GROUP],
                no_collision_group=obj[bl.RIGID_INTERSECTION_GROUP],
                bone_index=boneIndex,
                shape_position=common.Vector3(
                    obj.location.x-bone.pos[0],
                    obj.location.z-bone.pos[2],
                    obj.location.y-bone.pos[1]),
                shape_rotation=common.Vector3(
                    -obj.rotation_euler[0],
                    -obj.rotation_euler[2],
                    -obj.rotation_euler[1]),
                shape_type=shape_type,
                shape_size=shape_size,
                mass=obj[bl.RIGID_WEIGHT],
                linear_damping=obj[bl.RIGID_LINEAR_DAMPING],
                angular_damping=obj[bl.RIGID_ANGULAR_DAMPING],
                restitution=obj[bl.RIGID_RESTITUTION],
                friction=obj[bl.RIGID_FRICTION],
                mode=obj[bl.RIGID_PROCESS_TYPE]
                )
        model.rigidbodies.append(rigidBody)

    # constraint
    model.joints=[pmd.Joint(
        name=obj[bl.CONSTRAINT_NAME].encode('cp932'),
        rigidbody_index_a=rigidNameMap[obj[bl.CONSTRAINT_A]],
        rigidbody_index_b=rigidNameMap[obj[bl.CONSTRAINT_B]],
        position=common.Vector3(
            obj.location[0], 
            obj.location[2], 
            obj.location[1]),
        rotation=common.Vector3(
            -obj.rotation_euler[0], 
            -obj.rotation_euler[2], 
            -obj.rotation_euler[1]),
        translation_limit_min=common.Vector3(
            obj[bl.CONSTRAINT_POS_MIN][0],
            obj[bl.CONSTRAINT_POS_MIN][1],
            obj[bl.CONSTRAINT_POS_MIN][2]
            ),
        translation_limit_max=common.Vector3(
            obj[bl.CONSTRAINT_POS_MAX][0],
            obj[bl.CONSTRAINT_POS_MAX][1],
            obj[bl.CONSTRAINT_POS_MAX][2]
            ),
        rotation_limit_min=common.Vector3(
            obj[bl.CONSTRAINT_ROT_MIN][0],
            obj[bl.CONSTRAINT_ROT_MIN][1],
            obj[bl.CONSTRAINT_ROT_MIN][2]),
        rotation_limit_max=common.Vector3(
            obj[bl.CONSTRAINT_ROT_MAX][0],
            obj[bl.CONSTRAINT_ROT_MAX][1],
            obj[bl.CONSTRAINT_ROT_MAX][2]),
        spring_constant_translation=common.Vector3(
            obj[bl.CONSTRAINT_SPRING_POS][0],
            obj[bl.CONSTRAINT_SPRING_POS][1],
            obj[bl.CONSTRAINT_SPRING_POS][2]),
        spring_constant_rotation=common.Vector3(
            obj[bl.CONSTRAINT_SPRING_ROT][0],
            obj[bl.CONSTRAINT_SPRING_ROT][1],
            obj[bl.CONSTRAINT_SPRING_ROT][2])
        )
        for obj in self.oneSkinMesh.constraints]

    # 書き込み
    bl.message('write: %s' % path)
    return writer.write(io.open(path, 'wb'), model)


def _execute(filepath):
    active=bl.object.getActive()
    if not active:
        print("abort. no active object.")
        return

    exporter=oneskinmesh.Exporter()
    exporter.setup()

    model=create_pmx(exporter)
    bl.object.activate(active)
    with io.open(filepath, 'wb') as f:
        writer.write(f, model)
    return {'FINISHED'}

