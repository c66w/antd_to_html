"""Endpoints for serving HTML pages with OSS fallback."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

import aiohttp
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, FileResponse
from urllib.parse import urljoin

router = APIRouter(tags=["html-pages"])
logger = logging.getLogger(__name__)


def _get_oss_config() -> tuple[str, str, bool]:
  """Get OSS configuration from environment variables."""
  oss_domain = os.getenv("OSS_DOMAIN", "").rstrip('/')
  oss_prefix_raw = os.getenv("OSS_PREFIX", "html_pages/").rstrip('/')
  
  # 与 file_saver.py 保持一致：在 OSS_PREFIX 后添加 output/
  if oss_prefix_raw:
    oss_prefix = oss_prefix_raw.rstrip('/') + '/output/'
  else:
    oss_prefix = "html_pages/output/"
  
  use_oss_fallback = os.getenv("USE_OSS_FALLBACK", "true").lower() == "true"
  
  return oss_domain, oss_prefix, use_oss_fallback


@router.get("/html_pages/{path:path}")
@router.head("/html_pages/{path:path}")
async def serve_html_pages(request: Request, path: str) -> Response:
  """Serve HTML pages with local file fallback to OSS."""
  # 获取项目根目录
  current_file = Path(__file__).resolve()
  project_root = current_file.parent.parent.parent.parent  # api -> antd_to_html -> src -> project root
  output_dir = project_root / "output" / "html_pages"
  
  # 确保目录存在
  output_dir.mkdir(parents=True, exist_ok=True)
  
  # 获取 OSS 配置
  oss_domain, oss_prefix, use_oss_fallback = _get_oss_config()
  
  # 构建本地文件路径
  local_file_path = output_dir / path
  
  logger.info(f"Request for path: {path}, local_file_path: {local_file_path}, exists: {local_file_path.exists()}")
  logger.info(f"OSS config: domain={oss_domain}, prefix={oss_prefix}, fallback={use_oss_fallback}")
  
  # 检查本地文件是否存在
  if local_file_path.exists() and local_file_path.is_file():
    logger.info(f"Serving local file: {local_file_path}")
    return FileResponse(str(local_file_path))
  
  # 如果本地文件不存在，尝试从 OSS 获取
  if oss_domain and use_oss_fallback:
    # 构建 OSS 路径
    oss_path = f"{oss_prefix.rstrip('/')}/{path}"
    oss_url = urljoin(oss_domain + "/", oss_path)
    
    # 如果有查询参数，添加到 URL
    if request.url.query:
      oss_url = f"{oss_url}?{request.url.query}"
    
    logger.info(f"Local file not found, proxying to OSS: {path} -> {oss_url}")
    
    try:
      # 使用 aiohttp 转发请求
      timeout = aiohttp.ClientTimeout(total=30.0)
      # 转发请求头（排除一些不需要的）
      headers = dict(request.headers)
      headers.pop("host", None)
      headers.pop("connection", None)
      
      async with aiohttp.ClientSession(timeout=timeout) as session:
        # 发送请求到 OSS
        async with session.get(
          oss_url,
          headers=headers,
          allow_redirects=True
        ) as response:
          if response.status == 200:
            # 获取响应内容
            content = await response.read()
            
            # 获取响应内容类型
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            
            # 返回响应
            return StreamingResponse(
              iter([content]),
              status_code=response.status,
              headers={
                "Content-Type": content_type,
                "Cache-Control": "public, max-age=3600",  # 缓存 1 小时
              }
            )
          else:
            logger.warning(f"OSS returned non-200 status: {oss_url}, status: {response.status}")
            return Response("File not found", status_code=404)
    except aiohttp.ClientError as e:
      logger.error(f"OSS request failed: {oss_url}, error: {e}")
      return Response(f"Proxy error: {str(e)}", status_code=502)
    except asyncio.TimeoutError:
      logger.error(f"OSS request timeout: {oss_url}")
      return Response("Request timeout", status_code=504)
    except Exception as e:
      logger.error(f"OSS proxy exception: {oss_url}, error: {e}")
      return Response(f"Internal error: {str(e)}", status_code=500)
  
  # 如果 OSS 也未配置或失败，返回 404
  logger.warning(f"File not found locally and OSS not configured or disabled. path={path}, oss_domain={oss_domain}, use_oss_fallback={use_oss_fallback}")
  return Response("File not found", status_code=404)


@router.get("/html_pages")
@router.head("/html_pages")
async def serve_html_pages_root(request: Request) -> Response:
  """Serve HTML pages root, redirect to index.html."""
  return await serve_html_pages(request, "index.html")

