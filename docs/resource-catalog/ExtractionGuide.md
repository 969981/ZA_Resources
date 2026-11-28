# 全量资源普查与本地提取

[返回总览](README.md) · [[ImageResourceMapping]] · [[ModelResourceMapping]] · [[MapResourceMapping]]

在仓库根目录运行 Python 3.12：
```powershell
python scripts/Build-ZACompleteResourceCatalog.py --self-test
python scripts/Build-ZACompleteResourceCatalog.py --out .za-work/ZACompleteResources
```
使用 git ls-tree -rz 固定 commit 读取原生 virtual 路径，无需读取大 blob。包括未知文件；不混入 virtual_converted、原始 NCA、工具文件。多卷合并为逻辑文件但尾卷完整性未经证明。输出须为空目录，禁止覆盖已有结果。
生成 inventory.csv、category-summary.csv、summary.json，以及 ZAResourceDatabase/catalog.sqlite、images.sqlite、models.sqlite、maps.sqlite、pokemon.sqlite、localization.sqlite。三套分类目录自动创建但无素材时为空。SQLite resource/storage/mapping 分层；mapping 初始为空，SHA256/像素/格式/ID 未验证字段留 NULL。source_index 可反查物理文件。分类证据 CANDIDATE；路径存在为 CONFIRMED。

本地图片解码沿用原有脚本（需要已检出的源数据与合法使用权限）：
```powershell
python -m pip install Pillow==12.3.0
python scripts/Build-ZAImageResources.py --self-test
python scripts/Build-ZAImageResources.py --out .za-work/ZAImageResources-PNG --export
```
旧图片库尚未导入新的 catalog.sqlite。保留其像素及 ARC 成员证据，后续按原始路径和 BRTI 名关联；不能仅按文件名合并。CI 只上传元数据，不上传 PNG/GLB/原始资源。
