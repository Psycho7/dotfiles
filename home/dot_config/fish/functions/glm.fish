function glm
    # authentic
    set -fx ANTHROPIC_AUTH_TOKEN $Z_AI_API_KEY
    set -fx ANTHROPIC_BASE_URL https://api.z.ai/api/anthropic 
    set -fx API_TIMEOUT_MS 3000000
    set -fx CLAUDE_CODE_AUTO_COMPACT_WINDOW 1000000
    set -fx CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC 1

    # Set model mapping
    set -fx ANTHROPIC_DEFAULT_HAIKU_MODEL glm-5.3-flash[1m]
    set -fx ANTHROPIC_DEFAULT_SONNET_MODEL glm-5.3-flash[1m]
    set -fx ANTHROPIC_DEFAULT_OPUS_MODEL glm-5.3[1m]

    claude $argv
end
