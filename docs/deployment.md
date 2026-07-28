# Cognita — Deployment
1. `cd infra/terraform && terraform apply` → note `redis_url`, `app_role_arn`, `ecr_image_uri`.
2. Build & push image to ECR.
3. Create K8s secret `cognita-secrets` (or wire External Secrets to `env-bundle`).
4. `helm upgrade --install cognita ./helm/knowledge-ai-agent -n production --set image.repository=<ecr> --set image.tag=<sha> --set config.REDIS_URL=<redis_url>`.
5. Seed: `kubectl exec deploy/cognita-... -- python scripts/seed_data.py`.
