"""
Curated skill taxonomy for deterministic skill matching.
500+ terms across 15 categories. Used by the skill matcher tool
alongside LLM-based extraction for hybrid accuracy.
"""

SKILL_TAXONOMY: dict[str, list[str]] = {
    "languages": [
        "python", "javascript", "typescript", "java", "c++", "c#", "c",
        "go", "golang", "rust", "ruby", "php", "swift", "kotlin",
        "scala", "r", "matlab", "perl", "lua", "dart", "elixir",
        "haskell", "clojure", "groovy", "objective-c", "shell",
        "bash", "powershell", "sql", "html", "css", "sass", "less",
    ],
    "frameworks_frontend": [
        "react", "reactjs", "react.js", "angular", "angularjs", "vue",
        "vuejs", "vue.js", "svelte", "next.js", "nextjs", "nuxt",
        "nuxtjs", "gatsby", "remix", "astro", "htmx", "jquery",
        "bootstrap", "tailwind", "tailwindcss", "material-ui", "mui",
        "chakra ui", "ant design", "shadcn",
    ],
    "frameworks_backend": [
        "django", "flask", "fastapi", "express", "expressjs", "nestjs",
        "spring", "spring boot", "springboot", "rails", "ruby on rails",
        "laravel", "asp.net", ".net", "dotnet", "gin", "fiber",
        "actix", "phoenix", "koa", "hapi", "tornado", "sanic",
        "pyramid", "bottle", "aiohttp", "starlette",
    ],
    "databases": [
        "postgresql", "postgres", "mysql", "mariadb", "sqlite",
        "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
        "couchdb", "neo4j", "influxdb", "timescaledb", "cockroachdb",
        "supabase", "firebase", "firestore", "oracle", "sql server",
        "mssql", "memcached", "rethinkdb",
    ],
    "cloud_platforms": [
        "aws", "amazon web services", "azure", "microsoft azure",
        "gcp", "google cloud", "google cloud platform", "digitalocean",
        "heroku", "vercel", "netlify", "cloudflare", "linode",
        "vultr", "oracle cloud", "ibm cloud", "alibaba cloud",
        "render", "railway", "fly.io",
    ],
    "devops_infra": [
        "docker", "kubernetes", "k8s", "terraform", "ansible",
        "puppet", "chef", "vagrant", "helm", "istio", "nginx",
        "apache", "caddy", "traefik", "haproxy", "consul",
        "vault", "packer", "pulumi", "cloudformation", "cdk",
        "serverless", "lambda", "ecs", "eks", "fargate",
    ],
    "ci_cd": [
        "jenkins", "github actions", "gitlab ci", "circleci",
        "travis ci", "teamcity", "bamboo", "azure devops",
        "argo cd", "argocd", "spinnaker", "drone", "buildkite",
        "bitbucket pipelines", "codepipeline",
    ],
    "data_ml": [
        "machine learning", "deep learning", "tensorflow",
        "pytorch", "keras", "scikit-learn", "sklearn", "pandas",
        "numpy", "scipy", "matplotlib", "seaborn", "plotly",
        "jupyter", "huggingface", "transformers", "langchain",
        "openai", "llm", "nlp", "natural language processing",
        "computer vision", "opencv", "spark", "pyspark",
        "hadoop", "airflow", "dbt", "snowflake", "databricks",
        "tableau", "power bi", "looker", "metabase", "grafana",
        "mlflow", "wandb", "kubeflow", "ray", "dask",
    ],
    "testing": [
        "pytest", "unittest", "jest", "mocha", "chai", "cypress",
        "selenium", "playwright", "puppeteer", "junit", "testng",
        "rspec", "minitest", "phpunit", "xunit", "nunit",
        "postman", "insomnia", "k6", "locust", "jmeter",
        "tdd", "bdd", "cucumber",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira",
        "confluence", "slack", "trello", "asana", "notion",
        "figma", "sketch", "adobe xd", "invision", "zeplin",
        "postman", "swagger", "openapi", "graphql",
        "grpc", "protobuf", "rabbitmq", "kafka", "celery",
        "sqs", "sns", "pubsub", "websocket", "socket.io",
        "redis", "nginx", "linux", "unix", "vim", "vscode",
    ],
    "security": [
        "oauth", "oauth2", "jwt", "saml", "openid connect",
        "ssl", "tls", "https", "cors", "csrf", "xss",
        "owasp", "penetration testing", "vulnerability assessment",
        "soc2", "hipaa", "gdpr", "pci dss", "encryption",
        "iam", "rbac", "zero trust",
    ],
    "mobile": [
        "react native", "flutter", "swift", "swiftui", "kotlin",
        "android", "ios", "xamarin", "ionic", "capacitor",
        "expo", "cordova", "nativescript",
    ],
    "architecture": [
        "microservices", "monolith", "serverless", "event-driven",
        "rest", "rest api", "restful", "graphql", "grpc",
        "websockets", "message queue", "pub/sub", "cqrs",
        "event sourcing", "domain driven design", "ddd",
        "hexagonal architecture", "clean architecture",
        "solid", "design patterns", "api gateway",
        "load balancer", "cdn", "caching", "distributed systems",
    ],
    "methodologies": [
        "agile", "scrum", "kanban", "lean", "waterfall",
        "devops", "devsecops", "sre", "site reliability",
        "pair programming", "code review", "continuous integration",
        "continuous deployment", "continuous delivery",
        "gitflow", "trunk based development",
    ],
    "soft_skills": [
        "leadership", "team lead", "mentoring", "communication",
        "problem solving", "critical thinking", "collaboration",
        "project management", "stakeholder management",
        "presentation", "public speaking", "technical writing",
        "cross-functional", "self-motivated", "detail-oriented",
    ],
}


def get_all_skills_flat() -> list[str]:
    """Return a flat list of all skills across all categories."""
    skills = []
    for category_skills in SKILL_TAXONOMY.values():
        skills.extend(category_skills)
    return skills


def get_category_for_skill(skill: str) -> str | None:
    """Find which category a skill belongs to."""
    skill_lower = skill.lower()
    for category, skills in SKILL_TAXONOMY.items():
        if skill_lower in [s.lower() for s in skills]:
            return category
    return None
