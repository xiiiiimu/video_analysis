FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SKILLS_DIR=/app/skills \
    RUBRIC_DIR=/app/knowledge/rubric

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

# Skill SOP 文件：SkillLoader 通过 SKILLS_DIR 读取（pip install . 后不能再用源码相对路径）
COPY skills ./skills
# 内置评分点（md）；docker-compose 会把本地目录挂载到这里，改 md 后 restart 即可生效
COPY knowledge ./knowledge

RUN useradd --create-home --uid 10001 agent
USER agent

EXPOSE 8090

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8090/api/v1/agent/health', timeout=3).status == 200 else 1)"

CMD ["python", "-m", "agent_service.main"]
