# ZANativeModelExporter V1
[总览](README.md) · [网格/蒙皮](GeometrySkinLayerMask.md)
## 上轮验收
[46100679952](https://github.com/969981/ZA_Resources/actions/runs/46100679952) 成功：590 models，2348 pairs，11888 shapes，5643569 vertices，11190182 positive influences。DIRECT_RIG_ONLY 11446，BOTH 388，LOCAL_ONLY 4，NEITHER 50，314 shape issues。0 top-level errors 不代表所有 shape 通过。Artifact 15244983903。禁止无条件全量导出。
## Bind pose 原生数值实证
pm0001_00_00.trskl Git blob 7602c47972ae49eb8c29eaf5bb7a162888a8b128，114 nodes / 91 rigs。测试六种 Euler order、正负角、原生矩阵轴转置两种解释；最佳 Rz@Ry@Rx，弧度、T@R@S、parentWorld@local、原生 Vec3 axes 作为列。91/91 world@nativeInverseBind≈I，最大元素绝对误差 1.4415927724e-7，mean per-joint max 6.8906916934e-8；其他顺序明显不匹配。独立原版矩阵作为证据，非用计算矩阵自身求逆的循环验证。其他模型的 pivot/segment-scale compensation/rig offset 尚需全量对账；非零 pivot 保守拒绝。
## V1 功能
只允许妙蛙种子 LOD0；从真实 TRMDL/TRMSH/TRMBF/TRSKL/TRMMT/TRMTR 构建两个 GLB，position、normal、UV、uint16 index、JOINTS_0、WEIGHTS_0、114 transform nodes、91 joint inverse bind、6 primitive/4 materials。逐顶点验证索引/权重，原生 inverse bind 写入 glTF column-major MAT4。normal/rare 材质分支来自原版 TRMMT；V1 用 BaseColorLayer1/基础颜色作为可视化近似，保留原生参数和纹理路径在 extras，**不烘焙 BNTX，不宣称原版异色渲染**。无 tangent、动画、坐标/UV/视觉 parity；三角列表与 normal 分量仍待外部验证。GLB 自带结构检查及序列化后重新验证 bind，尚未跑 Khronos validator。
## LayerMask 下一步
原生 pm0001 四材质 shader=IkCharacter，NumMaterialLayer=5，BaseColorMultiply=True，LayerMaskScale1..4=1。body_b UVScaleOffset=(2,1,0,0)，eye UVCenter0=(0.5,0.5,0,0)。不能直接同坐标混合基础贴图与遮罩；先恢复 BNTX 多 mip 顶层、sRGB、swizzle、UV、采样；对照原版 Shader，再导出 baseColorTexture。参考 gftool 不是原版 Shader。
## 本地复现
```powershell
python -m pip install numpy==2.2.6
python scripts/ZANativeModelExporter.py --self-test
python scripts/ZANativeModelExporter.py --audit-all-bind --out .za-work/ZABindPoseAudit
python scripts/ZANativeModelExporter.py
```
本地输出 .za-work/ZANativeModelExporterV1/pm0001_00_00_normal.glb、pm0001_00_00_rare.glb、summary.json。CI 实际构建/检查 GLB 但按原仓库规则仅上传元数据，不上传游戏模型。全量 bind CI 独立执行，统计 PASS/FAIL/unsupported；未经验收不得批量导出。
