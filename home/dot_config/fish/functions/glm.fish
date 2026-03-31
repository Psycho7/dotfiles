function glm
    # authentic
    set -fx ANTHROPIC_AUTH_TOKEN $Z_AI_API_KEY
    set -fx ANTHROPIC_BASE_URL https://api.z.ai/api/anthropic 
    set -fx API_TIMEOUT_MS 3000000 

    # Set model mapping
    set -fx ANTHROPIC_DEFAULT_HAIKU_MODEL glm-4.7
    set -fx ANTHROPIC_DEFAULT_SONNET_MODEL glm-5.1
    set -fx ANTHROPIC_DEFAULT_OPUS_MODEL glm-5.1

    claude $argv
end
