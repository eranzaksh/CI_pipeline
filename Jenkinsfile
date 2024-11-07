pipeline {
    
    environment {
        registry = "eranzaksh/infinity" 
        registryCredential = 'docker-hub' 
        containerId = ''
        GIT_COMMIT = ''
        API_KEY = credentials('visual-crossing-api')
    }


    agent {
        docker {
            label 'eee'
            image "eranzaksh/jenkins-agent:python"
            args '-u 0:0 -v /var/run/docker.sock:/var/run/docker.sock'
            alwaysPull true
        }
    }

    stages {
        stage("Clone Git Repository") {
            steps {
                checkout scm
            }
        }
        
        // stage("Verify") {
        //     parallel {
                
        //         stage("Linting") {
        //             steps {
        //                 sh '/venv/bin/pylint --disable=E0401 --output-format=parseable --fail-under=5 web_app/'
        //             }
        //         }
                
        //         stage("Dependencies scan") {
        //             steps {
        //                 sh '/venv/bin/bandit -r web_app/. --severity-level high'
        //             }
        //         }
                
        //         stage("dockerfile scan") {
        //             steps {
        //                 sh '/venv/bin/checkov -f web_app/dockerfile --skip-check CKV_DOCKER_2 --skip-check CKV_DOCKER_3 --framework dockerfile'
        //             }
        //         }
        //     }
        // }
        stage("Build") {
            steps {
                script {
                    // because of "detected dubious ownership"
                    sh "git config --global --add safe.directory '*'"
                    GIT_COMMIT = sh (script: "git log -n 1 --pretty=format:'%H'", returnStdout: true)
                    sh "docker build -t eranzaksh/infinity:$BUILD_NUMBER-$GIT_COMMIT -t eranzaksh/infinity:latest web_app/."

                }
            }
        }

       stage("Test") {
           steps {
               script{
                    // Run the Docker container and capture the container ID
                    def containerId = sh(script: 'docker run -d -p 5001:5001 eranzaksh/infinity:latest', returnStdout: true).trim()
                    
                    // Wait for the container to start
                    sh 'sleep 3'

                    // Fetch the private IP of the EC2 instance
                    def privateIP = sh(
                        script: "curl -s http://169.254.169.254/latest/meta-data/local-ipv4",
                        returnStdout: true
                    ).trim()

                    // Check the connectivity by hitting the exposed endpoint
                    def status_code = sh(script: "curl -o /dev/null -s -w \"%{http_code}\" http://${privateIP}:5001", returnStdout: true).trim()
                    
                    // Validate the status code
                    if (status_code != '200') {
                        error "Connectivity test failed, expected 200 but got ${status_code}"
                    } else {
                        echo "Connectivity test passed with status code 200"
                    }
                    sh "docker stop $containerId"
                    sh "docker rm $containerId"
                    
               }
           }
       }
        stage('Push') { 
            steps { 
                script { 
                    docker.withRegistry( '', registryCredential ) { 
                        sh "docker push eranzaksh/infinity:$BUILD_NUMBER-$GIT_COMMIT"
                        sh 'docker push eranzaksh/infinity:latest'
                  }
                }
            }
        }
        stage('Trigger project-cd Job') {
            steps {
                script {

                    // Trigger the second job and pass the parameter
                    build job: 'project-cd', 
                          parameters: [string(name: 'GIT_COMMIT', value: "${GIT_COMMIT}")]
                }
            }
        }
    }     
    post {
        always {
        //      /* Always remove container */
        //     script { 
        //         sh "docker stop $containerId"
        //         sh "docker rm $containerId"
        //      }
            cleanWs() 
         }
        success {
          slackSend channel: 'succeeded-build', color: 'good', message: "Build successful: Job '${env.JOB_NAME}-${env.BUILD_NUMBER} ${STAGE_NAME}'"
        }
    
        failure {
          slackSend channel: 'devops-alerts', color: 'danger', message: "Build failed: Job '${env.JOB_NAME}-${env.BUILD_NUMBER} ${STAGE_NAME}'"
        }

}
    
}
