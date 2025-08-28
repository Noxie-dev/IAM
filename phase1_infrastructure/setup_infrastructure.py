#!/usr/bin/env python3
"""
Infrastructure Setup Script
Phase 1: Automated setup of PostgreSQL, Redis, and S3 storage

This script automates the setup and configuration of the infrastructure components
for the IAM SaaS platform migration.
"""

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
import psycopg2
import redis
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('infrastructure_setup.log')
    ]
)
logger = logging.getLogger(__name__)

class InfrastructureSetup:
    """
    Automated infrastructure setup and configuration
    """
    
    def __init__(self, config_file: str = '.env.infrastructure'):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_results = {}
    
    def load_config(self) -> Dict[str, str]:
        """Load configuration from environment file"""
        config = {}
        config_path = Path(__file__).parent / self.config_file
        
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    def run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run shell command with logging"""
        logger.info(f"Running command: {' '.join(command)}")
        
        try:
            result = subprocess.run(
                command,
                check=check,
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                logger.debug(f"Command output: {result.stdout}")
            
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            raise
    
    def check_docker(self) -> bool:
        """Check if Docker is installed and running"""
        try:
            result = self.run_command(['docker', '--version'], check=False)
            if result.returncode != 0:
                logger.error("Docker is not installed")
                return False
            
            result = self.run_command(['docker', 'info'], check=False)
            if result.returncode != 0:
                logger.error("Docker daemon is not running")
                return False
            
            logger.info("Docker is available and running")
            return True
            
        except FileNotFoundError:
            logger.error("Docker command not found")
            return False
    
    def setup_docker_infrastructure(self) -> bool:
        """Set up Docker containers for PostgreSQL and Redis"""
        logger.info("Setting up Docker infrastructure...")
        
        try:
            # Check if Docker Compose is available
            self.run_command(['docker-compose', '--version'])
            
            # Copy environment file
            env_source = Path(__file__).parent / '.env.infrastructure'
            env_target = Path(__file__).parent / '.env'
            
            if env_source.exists():
                import shutil
                shutil.copy2(env_source, env_target)
                logger.info("Environment file copied for Docker Compose")
            
            # Start infrastructure services
            compose_file = Path(__file__).parent / 'docker-compose.infrastructure.yml'
            
            if not compose_file.exists():
                logger.error("Docker Compose file not found")
                return False
            
            # Start core services (postgres, redis)
            self.run_command([
                'docker-compose',
                '-f', str(compose_file),
                'up', '-d',
                'postgres', 'redis'
            ])
            
            # Wait for services to be ready
            logger.info("Waiting for services to start...")
            time.sleep(10)
            
            # Check service health
            postgres_healthy = self.check_postgres_health()
            redis_healthy = self.check_redis_health()
            
            if postgres_healthy and redis_healthy:
                logger.info("Docker infrastructure setup completed successfully")
                return True
            else:
                logger.error("Some services failed to start properly")
                return False
                
        except Exception as e:
            logger.error(f"Docker infrastructure setup failed: {e}")
            return False
    
    def check_postgres_health(self) -> bool:
        """Check PostgreSQL connection"""
        try:
            conn = psycopg2.connect(
                host=self.config.get('POSTGRES_HOST', 'localhost'),
                port=self.config.get('POSTGRES_PORT', '5432'),
                database=self.config.get('POSTGRES_DB', 'iam_saas'),
                user=self.config.get('POSTGRES_USER', 'iam_user'),
                password=self.config.get('POSTGRES_PASSWORD', 'secure_password_123')
            )
            
            cursor = conn.cursor()
            cursor.execute('SELECT version();')
            version = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            logger.info(f"PostgreSQL is healthy: {version}")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    def check_redis_health(self) -> bool:
        """Check Redis connection"""
        try:
            r = redis.Redis(
                host=self.config.get('REDIS_HOST', 'localhost'),
                port=int(self.config.get('REDIS_PORT', '6379')),
                password=self.config.get('REDIS_PASSWORD'),
                db=int(self.config.get('REDIS_DB', '0'))
            )
            
            r.ping()
            info = r.info()
            
            logger.info(f"Redis is healthy: version {info['redis_version']}")
            return True
            
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def setup_database_schema(self) -> bool:
        """Set up PostgreSQL database schema"""
        logger.info("Setting up database schema...")
        
        try:
            # Connect to PostgreSQL
            conn = psycopg2.connect(
                host=self.config.get('POSTGRES_HOST', 'localhost'),
                port=self.config.get('POSTGRES_PORT', '5432'),
                database=self.config.get('POSTGRES_DB', 'iam_saas'),
                user=self.config.get('POSTGRES_USER', 'iam_user'),
                password=self.config.get('POSTGRES_PASSWORD', 'secure_password_123')
            )
            
            # Read and execute schema file
            schema_file = Path(__file__).parent / 'database_setup.sql'
            
            if not schema_file.exists():
                logger.error("Database schema file not found")
                return False
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            cursor = conn.cursor()
            cursor.execute(schema_sql)
            conn.commit()
            
            cursor.close()
            conn.close()
            
            logger.info("Database schema setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Database schema setup failed: {e}")
            return False
    
    def migrate_sqlite_data(self) -> bool:
        """Migrate data from SQLite to PostgreSQL"""
        logger.info("Migrating data from SQLite...")
        
        try:
            # Import and run migration script
            sys.path.append(str(Path(__file__).parent))
            from migrate_sqlite_to_postgresql import DatabaseMigrator
            
            sqlite_path = Path(__file__).parent.parent / 'iam-backend' / 'src' / 'database' / 'app.db'
            
            postgres_config = {
                'host': self.config.get('POSTGRES_HOST', 'localhost'),
                'port': self.config.get('POSTGRES_PORT', '5432'),
                'database': self.config.get('POSTGRES_DB', 'iam_saas'),
                'user': self.config.get('POSTGRES_USER', 'iam_user'),
                'password': self.config.get('POSTGRES_PASSWORD', 'secure_password_123')
            }
            
            migrator = DatabaseMigrator(str(sqlite_path), postgres_config)
            results = migrator.run_migration()
            
            logger.info(f"Data migration completed: {results}")
            return True
            
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            return False
    
    def test_s3_storage(self) -> bool:
        """Test S3 storage configuration"""
        logger.info("Testing S3 storage configuration...")
        
        try:
            # Import S3 storage manager
            sys.path.append(str(Path(__file__).parent))
            from s3_storage_config import create_storage_manager
            
            # Set environment variables for S3 config
            os.environ.update({
                'S3_ENDPOINT_URL': self.config.get('S3_ENDPOINT_URL', ''),
                'S3_ACCESS_KEY': self.config.get('S3_ACCESS_KEY', ''),
                'S3_SECRET_KEY': self.config.get('S3_SECRET_KEY', ''),
                'S3_BUCKET_NAME': self.config.get('S3_BUCKET_NAME', 'iam-transcription-files'),
                'S3_REGION': self.config.get('S3_REGION', 'us-east-1')
            })
            
            # Test storage manager
            storage = create_storage_manager()
            
            # Test basic operations
            test_key = 'test/infrastructure_setup.txt'
            test_content = b'Infrastructure setup test file'
            
            # Upload test file
            from io import BytesIO
            test_file = BytesIO(test_content)
            result = storage.upload_file(test_file, test_key, 'text/plain')
            
            if result['success']:
                # Clean up test file
                storage.delete_file(test_key)
                logger.info("S3 storage test completed successfully")
                return True
            else:
                logger.error(f"S3 storage test failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"S3 storage test failed: {e}")
            logger.warning("S3 storage will need to be configured manually")
            return False
    
    def generate_summary_report(self) -> str:
        """Generate setup summary report"""
        report = []
        report.append("=" * 60)
        report.append("IAM SAAS INFRASTRUCTURE SETUP SUMMARY")
        report.append("=" * 60)
        
        for component, status in self.setup_results.items():
            status_icon = "✅" if status else "❌"
            report.append(f"{status_icon} {component}")
        
        report.append("")
        report.append("Next Steps:")
        report.append("1. Review and update configuration in .env.infrastructure")
        report.append("2. Configure S3 storage credentials if not done")
        report.append("3. Set up SSL certificates for production")
        report.append("4. Configure monitoring and alerting")
        report.append("5. Run Phase 2: Backend Enhancement")
        
        report.append("")
        report.append("Access URLs (Development):")
        report.append(f"- pgAdmin: http://localhost:{self.config.get('PGADMIN_PORT', '5050')}")
        report.append(f"- Redis Commander: http://localhost:{self.config.get('REDIS_COMMANDER_PORT', '8081')}")
        report.append(f"- PostgreSQL: localhost:{self.config.get('POSTGRES_PORT', '5432')}")
        report.append(f"- Redis: localhost:{self.config.get('REDIS_PORT', '6379')}")
        
        return "\n".join(report)
    
    def run_setup(self) -> bool:
        """Run complete infrastructure setup"""
        logger.info("Starting IAM SaaS infrastructure setup...")
        
        # Check prerequisites
        if not self.check_docker():
            logger.error("Docker is required but not available")
            return False
        
        # Setup steps
        setup_steps = [
            ("Docker Infrastructure", self.setup_docker_infrastructure),
            ("Database Schema", self.setup_database_schema),
            ("Data Migration", self.migrate_sqlite_data),
            ("S3 Storage Test", self.test_s3_storage),
        ]
        
        # Execute setup steps
        for step_name, step_function in setup_steps:
            logger.info(f"Executing: {step_name}")
            
            try:
                success = step_function()
                self.setup_results[step_name] = success
                
                if success:
                    logger.info(f"✅ {step_name} completed successfully")
                else:
                    logger.warning(f"⚠️ {step_name} completed with issues")
                    
            except Exception as e:
                logger.error(f"❌ {step_name} failed: {e}")
                self.setup_results[step_name] = False
        
        # Generate summary
        summary = self.generate_summary_report()
        logger.info("\n" + summary)
        
        # Write summary to file
        with open('infrastructure_setup_summary.txt', 'w') as f:
            f.write(summary)
        
        # Check overall success
        success_count = sum(1 for success in self.setup_results.values() if success)
        total_count = len(self.setup_results)
        
        if success_count == total_count:
            logger.info("🎉 Infrastructure setup completed successfully!")
            return True
        else:
            logger.warning(f"⚠️ Infrastructure setup completed with {total_count - success_count} issues")
            return False

def main():
    """Main setup function"""
    print("🚀 IAM SaaS Platform - Infrastructure Setup")
    print("=" * 50)
    
    setup = InfrastructureSetup()
    success = setup.run_setup()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("You can now proceed to Phase 2: Backend Enhancement")
    else:
        print("\n⚠️ Setup completed with some issues.")
        print("Please review the logs and fix any problems before proceeding.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
