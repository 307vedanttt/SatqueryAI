import pytest
from fastapi.testclient import TestClient
import numpy as np
import rasterio
from rasterio.transform import from_origin
import os
import tempfile
from io import BytesIO

from app.main import app
from app.models.schemas import ImageMetadata
from app.ingestion.validation import validate_pair, detect_sensor_configuration, ValidationResult

client = TestClient(app)

@pytest.fixture
def dummy_geotiff():
    fd, path = tempfile.mkstemp(suffix=".tif")
    os.close(fd)
    
    transform = from_origin(10.0, 20.0, 10.0, 10.0)
    data = np.zeros((1, 10, 10), dtype=rasterio.uint8)
    
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=data.shape[1],
        width=data.shape[2],
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(data)
        dst.update_tags(SENSOR="Sentinel-2", ACQUISITION_DATE="2023-01-01")
        
    yield path
    os.remove(path)

@pytest.fixture
def dummy_sar_geotiff():
    fd, path = tempfile.mkstemp(suffix=".tif")
    os.close(fd)
    
    transform = from_origin(10.0, 20.0, 10.0, 10.0)
    data = np.zeros((1, 10, 10), dtype=rasterio.float32)
    
    with rasterio.open(
        path,
        'w',
        driver='GTiff',
        height=data.shape[1],
        width=data.shape[2],
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform,
    ) as dst:
        dst.write(data)
        dst.update_tags(SENSOR="Sentinel-1", ACQUISITION_DATE="2023-01-01")
        
    yield path
    os.remove(path)

@pytest.fixture
def dummy_png():
    from PIL import Image
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img = Image.new('RGB', (60, 30), color = 'red')
    img.save(path)
    yield path
    os.remove(path)

def test_valid_geotiff(dummy_geotiff):
    with open(dummy_geotiff, "rb") as f:
        response = client.post(
            "/api/imagery/validate",
            files={"files": ("test.tif", f, "image/tiff")},
            data={"configuration": "single"}
        )
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True
    assert res["metadata"][0]["is_geotiff"] is True
    assert res["sensor_type"] == "optical"

def test_invalid_file():
    # Sending some text data instead of image
    response = client.post(
        "/api/imagery/validate",
        files={"files": ("test.txt", b"Hello World", "text/plain")},
        data={"configuration": "single"}
    )
    assert response.status_code == 400

def test_corrupted_raster():
    response = client.post(
        "/api/imagery/validate",
        files={"files": ("corrupted.tif", b"corrupted raster data", "image/tiff")},
        data={"configuration": "single"}
    )
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is False
    assert len(res["errors"]) > 0

def test_optical_metadata():
    meta = ImageMetadata(filename="opt.tif", sensor="Sentinel-2", is_geotiff=True)
    sensor, conf, src = detect_sensor_configuration(meta)
    assert sensor == "optical"

def test_sar_metadata():
    meta = ImageMetadata(filename="sar.tif", sensor="Sentinel-1", is_geotiff=True)
    sensor, conf, src = detect_sensor_configuration(meta)
    assert sensor == "sar"

def test_mismatched_optical_sar_pair():
    meta1 = ImageMetadata(filename="opt.tif", sensor="Sentinel-2", crs="EPSG:4326", bounds=(0,0,10,10), is_geotiff=True)
    meta2 = ImageMetadata(filename="sar.tif", sensor="Sentinel-1", crs="EPSG:3857", bounds=(20,20,30,30), is_geotiff=True)
    res = validate_pair(meta1, meta2, "optical_sar")
    assert not res.is_valid
    assert len(res.errors) > 0 # CRS mismatch and Bounds overlap

def test_valid_optical_sar_pair(dummy_geotiff, dummy_sar_geotiff):
    with open(dummy_geotiff, "rb") as f1, open(dummy_sar_geotiff, "rb") as f2:
        response = client.post(
            "/api/imagery/validate",
            files=[
                ("files", ("test1.tif", f1, "image/tiff")),
                ("files", ("test2.tif", f2, "image/tiff"))
            ],
            data={"configuration": "optical_sar"}
        )
    assert response.status_code == 200
    res = response.json()
    assert res["is_valid"] is True
    assert res["pair_validation"]["is_valid"] is True

def test_invalid_bi_temporal_pair():
    meta1 = ImageMetadata(filename="opt1.tif", sensor="Sentinel-2", crs="EPSG:4326", bounds=(0,0,10,10), is_geotiff=True)
    meta2 = ImageMetadata(filename="opt2.tif", sensor="Sentinel-2", crs="EPSG:4326", bounds=(20,20,30,30), is_geotiff=True)
    res = validate_pair(meta1, meta2, "bi_temporal")
    assert not res.is_valid # Spatial overlap issue

def test_oversized_upload(monkeypatch):
    from app.core import security
    monkeypatch.setattr(security, "MAX_FILE_SIZE", 10) # 10 bytes limit
    
    response = client.post(
        "/api/imagery/validate",
        files={"files": ("large.tif", b"A" * 100, "image/tiff")},
        data={"configuration": "single"}
    )
    assert response.status_code == 413

def test_unsupported_extension():
    response = client.post(
        "/api/imagery/validate",
        files={"files": ("unsupported.exe", b"MZ...", "application/x-msdownload")},
        data={"configuration": "single"}
    )
    assert response.status_code == 400

