# How to Get Your OpenAI API Key

This guide will walk you through getting an OpenAI API key to use with the troubleshooting agent.

## 📋 Prerequisites

- A valid email address
- A phone number for verification
- A payment method (credit/debit card)

## 🚀 Step-by-Step Guide

### Step 1: Create an OpenAI Account

1. **Go to OpenAI's website:**
   - Visit: https://platform.openai.com/signup

2. **Sign up:**
   - Click "Sign up"
   - Enter your email address
   - Create a password
   - Or sign up with Google/Microsoft account

3. **Verify your email:**
   - Check your email inbox
   - Click the verification link

4. **Complete your profile:**
   - Enter your name
   - Verify your phone number (you'll receive a code via SMS)

### Step 2: Set Up Billing

**Important:** OpenAI requires a payment method to use the API, even though they offer free credits for new users.

1. **Go to billing settings:**
   - Visit: https://platform.openai.com/account/billing/overview
   - Or click your profile → "Billing"

2. **Add payment method:**
   - Click "Add payment method"
   - Enter your credit/debit card information
   - Click "Add payment method"

3. **Set usage limits (recommended):**
   - Click "Usage limits"
   - Set a monthly budget (e.g., $10-$20 to start)
   - Set a notification threshold
   - This prevents unexpected charges

### Step 3: Create an API Key

1. **Go to API keys page:**
   - Visit: https://platform.openai.com/api-keys
   - Or click your profile → "API keys"

2. **Create new key:**
   - Click "+ Create new secret key"
   - Give it a name (e.g., "k8s-consul-agent")
   - Click "Create secret key"

3. **Copy your API key:**
   - **IMPORTANT:** Copy the key immediately!
   - You won't be able to see it again
   - It looks like: `sk-proj-...` (starts with `sk-`)
   - Store it securely

### Step 4: Add API Key to Your Project

1. **Navigate to your project:**
   ```bash
   cd /Users/chrislovett/Desktop/meshtrbl
   ```

2. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit the .env file:**
   ```bash
   nano .env
   # Or use your preferred editor: code .env, vim .env, etc.
   ```

4. **Add your API key:**
   ```bash
   OPENAI_API_KEY=sk-proj-your-actual-key-here
   ```

5. **Save and close the file:**
   - In nano: Press `Ctrl+X`, then `Y`, then `Enter`
   - In vim: Press `Esc`, type `:wq`, press `Enter`

6. **Verify it's set (optional):**
   ```bash
   cat .env | grep OPENAI_API_KEY
   # Should show: OPENAI_API_KEY=sk-proj-...
   ```

## 💰 Pricing Information

### Free Credits
- New users get **$5 in free credits**
- Valid for **3 months** from account creation
- Perfect for testing and development

### GPT-4 Turbo Pricing (Recommended Model)
- **Input:** $10 per 1M tokens (~750,000 words)
- **Output:** $30 per 1M tokens (~750,000 words)

### Typical Usage for This Agent
- **Simple query:** ~500-1,000 tokens = $0.01-$0.02
- **Complex troubleshooting:** ~2,000-5,000 tokens = $0.05-$0.15
- **Daily usage (10-20 queries):** ~$0.50-$2.00

### Cost-Saving Tips
1. **Use GPT-3.5-turbo for testing** (10x cheaper):
   - Edit `config/agent_config.yaml`
   - Change model to `gpt-3.5-turbo`
   - Or use `--model gpt-3.5-turbo` flag

2. **Set usage limits:**
   - Go to: https://platform.openai.com/account/limits
   - Set monthly budget
   - Enable email notifications

3. **Monitor usage:**
   - Check: https://platform.openai.com/usage
   - Review daily/monthly costs

## 🔐 Security Best Practices

### DO:
✅ Store API key in `.env` file (already in `.gitignore`)
✅ Use environment variables
✅ Set usage limits
✅ Rotate keys periodically
✅ Use separate keys for different projects

### DON'T:
❌ Commit API keys to git
❌ Share keys publicly
❌ Hardcode keys in source code
❌ Use the same key everywhere
❌ Share keys via email/chat

### If Your Key is Compromised:
1. Go to: https://platform.openai.com/api-keys
2. Click the trash icon next to the compromised key
3. Create a new key
4. Update your `.env` file

## 🧪 Testing Your API Key

Once you've added your API key, test it:

```bash
cd /Users/chrislovett/Desktop/meshtrbl

# Activate virtual environment
source venv/bin/activate

# Install dependencies (if not already done)
pip install -r requirements.txt

# Test with a simple query
python -m src.agent --query "Hello, can you help me?"
```

If it works, you'll see the agent respond!

## 🆘 Troubleshooting

### Error: "OpenAI API key must be provided"
**Solution:** Make sure your `.env` file exists and contains:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Error: "Incorrect API key provided"
**Solutions:**
- Verify you copied the entire key (starts with `sk-`)
- Check for extra spaces or quotes
- Make sure the key hasn't been revoked
- Create a new key if needed

### Error: "You exceeded your current quota"
**Solutions:**
- Check your billing: https://platform.openai.com/account/billing
- Add a payment method
- Wait for free credits to refresh (if applicable)
- Check usage limits

### Error: "Rate limit exceeded"
**Solutions:**
- Wait a few seconds and try again
- You're making too many requests too quickly
- Consider upgrading your plan for higher limits

## 📊 Monitoring Usage

### View Usage Dashboard:
https://platform.openai.com/usage

### Check Current Costs:
```bash
# View usage for current month
# Go to: https://platform.openai.com/account/usage
```

### Set Up Alerts:
1. Go to: https://platform.openai.com/account/billing/limits
2. Set "Email notification threshold"
3. Set "Hard limit" (optional)

## 🔄 Alternative: Using Other LLM Providers

If you prefer not to use OpenAI, you can modify the agent to use:

### 1. Anthropic Claude
- Get API key: https://console.anthropic.com/
- Modify `src/agent.py` to use `langchain-anthropic`

### 2. Local LLMs (Free!)
- Use Ollama: https://ollama.ai/
- Run models locally (no API key needed)
- Modify agent to use local endpoint

### 3. Azure OpenAI
- Use Azure's OpenAI service
- Get credentials from Azure Portal
- Modify connection settings

## 📚 Additional Resources

- **OpenAI Platform Docs:** https://platform.openai.com/docs
- **API Reference:** https://platform.openai.com/docs/api-reference
- **Pricing:** https://openai.com/pricing
- **Usage Policies:** https://openai.com/policies/usage-policies
- **Community Forum:** https://community.openai.com/

## ✅ Quick Checklist

- [ ] Created OpenAI account
- [ ] Verified email and phone
- [ ] Added payment method
- [ ] Set usage limits
- [ ] Created API key
- [ ] Copied API key securely
- [ ] Created `.env` file
- [ ] Added API key to `.env`
- [ ] Tested the agent
- [ ] Set up usage monitoring

---

**Once you have your API key set up, you're ready to start using the agent!** 🚀

For usage instructions, see [QUICKSTART.md](QUICKSTART.md)