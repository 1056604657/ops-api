from django.shortcuts import render
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
import os
from pathlib import Path
from . import models, serializers
import re
from django.http import JsonResponse
from .config.config import cluster_map
from .config.config import jenkins_auths
from .config.config import base_image
from datetime import datetime
import jenkins
import xml.sax.saxutils as saxutils

def create_jenkins_pipeline(jenkins_url, username, token, job_name, pipeline_script, description=''):
    """
    创建Jenkins Pipeline作业（使用嵌入式脚本）
    """
    # 连接Jenkins服务器
    server = jenkins.Jenkins(jenkins_url, username=username, password=token)
    
    # 对Pipeline脚本进行XML转义
    escaped_script = saxutils.escape(pipeline_script)
    
    # Pipeline作业的配置XML
    pipeline_config = f'''<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
    <description>通过API创建的Pipeline作业</description>
    <keepDependencies>false</keepDependencies>
    <definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition" plugin="workflow-cps">
        <script>{escaped_script}</script>
        <sandbox>true</sandbox>
    </definition>
</flow-definition>'''

    try:
        if server.job_exists(job_name):
            print(f"Jenkins作业 {job_name} 在 {jenkins_url} 环境中已存在")
            return False
            
        server.create_job(job_name, pipeline_config)
        print(f"成功创建Pipeline作业: {job_name}")
        return True
        
    except Exception as e:
        error_msg = f"创建作业失败: {str(e)}"
        print(error_msg)
        return False


def delete_jenkins_pipeline(jenkins_url, username, token, job_name):
    """
    删除Jenkins Pipeline作业（使用嵌入式脚本）
    """
    # 连接Jenkins服务器
    server = jenkins.Jenkins(jenkins_url, username=username, password=token)
    
    try:
        server.delete_job(job_name)
        print(f"成功删除Pipeline作业: {job_name}")
        return True
    except Exception as e:
        error_msg = f"删除作业失败: {str(e)}"
        print(error_msg)
        return False




class TemplateGeneratorViewSet(ModelViewSet):
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    # 处理 nodejs jenkinsfile 的方法
    def process_nodejs_jenkinsfile(self, content, params):
        """处理 Jenkinsfile 内容"""
        # 处理 git URL
        if 'giturl' in params:
            pattern = r"url:\s*'[^']*'"
            replacement = f"url: '{params['giturl']}'"
            content = re.sub(pattern, replacement, content)
        
        # 处理 mvn 命令
        if 'mvn_command' in params:
            pattern = r"sh\s*'mvn\s+-f\s+[^']*'"
            replacement = f"sh '{params['mvn_command']}'"
            content = re.sub(pattern, replacement, content)
        
        return content

    # 处理 go jenkinsfile 的方法
    def process_go_jenkinsfile(self, content, params):
        """处理 Jenkinsfile 内容"""
        # 处理 git URL
        if 'giturl' in params:
            pattern = r"url:\s*'[^']*'"
            replacement = f"url: '{params['giturl']}'"
            content = re.sub(pattern, replacement, content)
        
        return content

    # 处理 java jenkinsfile 的方法
    def process_java_jenkinsfile(self, content, params, yaml_content=None, current_env=None):
        service_name = params.get('serviceName', '')
        
        replacements = {
            '##gitUrl##': params.get('gitUrl', ''),
            '##jdkVersion##': params.get('jdkVersion', 'jdk8'),
            '##pomDir##': params.get('pomDir', './'),
            '##serviceName##': service_name,
            '##namespace##': params.get('namespace', ''),
            '##cluster##': params.get('cluster', ''),
            '##jumpServer##': params.get('jump_server', ''),
            '##kubeConfig##': params.get('kube_config', ''),
            '##okApiPath##': params.get('okApiPath', '/ok'),
            '##credentialsId##': params.get('credentialsId', ''),
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        tag_cmd = f"""tag=$(echo $Branch | awk -F '/' '{{print $2}}')_$(date +%Y%m%d_%H%M)
                    cp /mnt/shell/docker/push_allinone.sh {params.get('pomDir', './')}target/*.jar .
                    
                    cat > Dockerfile << 'EOF'
FROM {base_image[params.get('jdkVersion')]}
RUN mkdir /usr/local/app -p &&\\
    mkdir /data
COPY *.jar /usr/local/app/app.jar
COPY LAST_COMMIT.log /usr/local/app
WORKDIR /usr/local/app
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
EOF

                    ./push_allinone.sh {params.get('cluster', '')}-{current_env} {params.get('image_namespace', '')}/{params.get('namespace', '')} {service_name} $tag
                    ./push_allinone.sh {params.get('cluster', '')}-live {params.get('cluster', '')}/{params.get('namespace', '')} {service_name} $tag
                    cat > {service_name}.yaml << 'EOL'
{yaml_content}
EOL

                    sed -i "s|:latest|:$tag|g" {service_name}.yaml"""
        pattern = r"tag=\$\(echo \$Branch.*?\n.*?cp /mnt/shell/docker/push_allinone\.sh.*?\n.*?\.\/push_allinone\.sh.*?\n"
        content = re.sub(pattern, tag_cmd + '\n', content, flags=re.DOTALL)
        if current_env == 'dev' or current_env == 'test':
            content = content.replace(f"./push_allinone.sh {params.get('cluster', '')}-live {params.get('cluster', '')}/{params.get('namespace', '')} {service_name} $tag", '')
        return content

    # 处理 python jenkinsfile 的方法
    def process_python_jenkinsfile(self, content, params):
        """处理 Jenkinsfile 内容"""
        # 处理 git URL
        if 'giturl' in params:
            pattern = r"url:\s*'[^']*'"
            replacement = f"url: '{params['giturl']}'"
            content = re.sub(pattern, replacement, content)
        
        return content
    
    # 处理 nodejs 的 yaml 的方法
    def process_nodejs_yaml(self, content, params):
        """处理 yaml 内容"""

    # 处理 go 的 yaml 的方法
    def process_go_yaml(self, content, params):
        """处理 yaml 内容"""
    
    # 处理 java 的 yaml 的方法
    def process_java_yaml(self, content, params):
        replacements = {
            '##serviceName##': params.get('serviceName', ''),
            '##namespace##': params.get('namespace', ''),
            '##okApiPath##': params.get('okApiPath', '/ok'),
            '##image_namespace##': params.get('image_namespace', '')
        }
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)
        return content

    # 处理 python 的 yaml 的方法
    def process_python_yaml(self, content, params):
        """处理 yaml 内容"""





    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        language = request.data.get('language')
        template_params = request.data.get('form', {})
        service_name = template_params.get('serviceName', '')
        
        res = {
            "code": 20000,
            "data": {},
            "message": "success to create jenkins job"
        }

        # 记录成功的环境
        success_envs = []

        try:
            base_path = Path(__file__).resolve().parent / 'config' / 'template' / language
            templates = {}
            
            cluster = template_params.get('cluster', '')
            # 获取所有的 jenkinsfile 和 yaml 文件
            jenkinsfiles = list(base_path.glob('jenkinsfile_*'))
            yamls = list(base_path.glob('yaml_*'))
        
            # 处理所有环境的 yaml 文件
            for yaml_path in yamls:
                current_env = yaml_path.name.split('_')[1]
                image_namespace = cluster_map[cluster]['image_namespace'][current_env] if current_env in cluster_map[cluster]['image_namespace'] else ''
                template_params['image_namespace'] = image_namespace
                with open(yaml_path, 'r') as f:
                    yaml_content = f.read()
                    process_yaml = getattr(self, f'process_{language}_yaml')
                    modified_yaml = process_yaml(yaml_content, template_params)
                    templates[yaml_path.name] = modified_yaml

            # 处理每个 jenkinsfile,并创建pipeline
            for jenkinsfile_path in jenkinsfiles:
                current_env = jenkinsfile_path.name.split('_')[1]
                jump_server = cluster_map[cluster]['jump_server'][current_env] if current_env in cluster_map[cluster]['jump_server'] else ''
                kube_config = cluster_map[cluster]['kube_config'][current_env] if current_env in cluster_map[cluster]['kube_config'] else ''
                credentials_id = jenkins_auths[current_env]['credentialsId']
                image_namespace = cluster_map[cluster]['image_namespace'][current_env] if current_env in cluster_map[cluster]['image_namespace'] else ''
                template_params['image_namespace'] = image_namespace
                template_params['jump_server'] = jump_server
                template_params['kube_config'] = kube_config
                template_params['credentialsId'] = credentials_id
                print(template_params)

                with open(jenkinsfile_path, 'r') as f:
                    jenkinsfile_content = f.read()
                try:
                    process_jenkinsfile = getattr(self, f'process_{language}_jenkinsfile')
                    modified_jenkinsfile = process_jenkinsfile(jenkinsfile_content, template_params, templates[f'yaml_{current_env}'], current_env)
                    templates[jenkinsfile_path.name] = modified_jenkinsfile

                    # 创建 Jenkins pipeline
                    if current_env in jenkins_auths:
                        jenkins_config = jenkins_auths[current_env]
                        create_result = create_jenkins_pipeline(
                            jenkins_url=jenkins_config['url'],
                            username=jenkins_config['username'],
                            token=jenkins_config['password'],
                            job_name=service_name,
                            pipeline_script=modified_jenkinsfile,
                            description=f"通过API创建的Pipeline作业"
                        )
                        
                        if not create_result:
                            res['code'] = 40000
                            res['message'] = f"在 {current_env} 环境创建Jenkins作业失败。已成功创建的环境：{', '.join(success_envs) if success_envs else '无'}"
                            return Response(res, status=status.HTTP_400_BAD_REQUEST)
                        
                        # Jenkins job创建成功，保存到数据库
                        models.PipelineJob.objects.create(
                            language=language,
                            service_name=service_name,
                            config={
                                **template_params,
                                'environment': current_env,
                                'jenkins_url': jenkins_config['url']
                            },
                            jenkinsfile=modified_jenkinsfile,
                            yaml_file=templates[f'yaml_{current_env}']
                        )
                        
                        # 记录成功的环境
                        success_envs.append(current_env)
                except ValueError as ve:
                    res['code'] = 40000
                    res['message'] = str(ve)
                    return Response(res, status=status.HTTP_400_BAD_REQUEST)

            # 在返回之前保存所有文件到本地
            output_dir = Path(__file__).resolve().parent / 'generated_files' / language
            output_dir.mkdir(parents=True, exist_ok=True)
            for existing_file in output_dir.glob('*'):
                existing_file.unlink()
            for filename, content in templates.items():
                file_path = output_dir / filename
                with open(file_path, 'w') as f:
                    f.write(content)
            print(f"Generated files saved to: {output_dir}")



            res['data'] = templates
            # 保存到数据库

        except Exception as e:
            res['code'] = 50000
            res['message'] = str(e)
            return Response(res, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return JsonResponse(res)


    # 获取数据库中所有的pipelinejob记录中的language和service_name列
    @action(detail=False, methods=['get'])
    def get_jenkinsjob_list(self, request):
        res = {
        "code": 20000,
        "data": {},
        "message": "success to get jenkinsjob list"
    }
        jenkinsjob_list = models.PipelineJob.objects.values('language', 'service_name', 'config', 'created_at')
        res['data'] = list(jenkinsjob_list)
        return JsonResponse(res)
    

    # 根据service_name和环境去数据库找config里的environment的相应列，然后获取这个环境的jenkinsfile列
    @action(detail=False, methods=['get'])
    def get_job_jenkinsfile(self, request):
        service_name = request.query_params.get('service_name')
        environment = request.query_params.get('environment')
        jenkinsfile = models.PipelineJob.objects.filter(service_name=service_name, config__environment=environment).values('jenkinsfile')
        return JsonResponse(list(jenkinsfile), safe=False)
    
    # 删除Jenkins作业
    @action(detail=False, methods=['post'])
    def delete_jenkinsjob(self, request):
        res = {
            "code": 20000,
            "message": ""
        }
        
        job_name = request.data.get('job_name')
        success_envs = []  # 存储成功删除的环境
        failed_envs = []   # 存储删除失败的环境
        
        for environment in jenkins_auths:
            username = jenkins_auths[environment]['username']
            token = jenkins_auths[environment]['password']
            jenkins_url = jenkins_auths[environment]['url']
            delete_result = delete_jenkins_pipeline(jenkins_url, username, token, job_name)
            delete_db_result = models.PipelineJob.objects.filter(service_name=job_name, config__environment=environment).delete()
            if delete_result and delete_db_result:
                success_envs.append(environment)
            else:
                failed_envs.append(environment)
        
        # 根据成功和失败情况设置返回信息
        if failed_envs:
            res['code'] = 40000
            res['message'] = f"删除作业部分失败,请手动删除。成功环境: {', '.join(success_envs) if success_envs else '无'}, 失败环境: {', '.join(failed_envs)}"
            return JsonResponse(res, status=status.HTTP_400_BAD_REQUEST)
        else:
            res['message'] = f"删除作业成功。成功环境: {', '.join(success_envs)}"
            return JsonResponse(res)
            