# Domain Setup Guide: ehub.co.tz

This guide explains how to add your domain to Linode's DNS system and configure the subdomain `eduka.ehub.co.tz`.

## Step 1: Add Domain to Linode (DNS Manager)

Even if you don't host the domain on a dedicated Linode server instance, you can use Linode's free DNS Manager.

1.  Log in to [Linode Cloud Manager](https://cloud.linode.com/).
2.  Click on **Domains** in the left sidebar.
3.  Click **Create Domain**.
4.  Fill in the form:
    *   **Domain**: `ehub.co.tz`
    *   **Email Address**: Your email address.
    *   **Insert Default Records**: You can selecting "Do not insert default records" (or select your server if you want generic records created).
5.  Click **Create Domain**.

## Step 2: Create the Subdomain (A Record)

Now we point `eduka.ehub.co.tz` to your project's server IP.

1.  In the Linode Domain Manager for `ehub.co.tz`, locate the **A/AAAA Records** section.
2.  Click **Add an A/AAAA Record**.
3.  Fill in the details:
    *   **Hostname**: `eduka`
        *   *Resulting FQDN will be `eduka.ehub.co.tz`*
    *   **IP Address**: Enter the IP address of your Linode server where the project is running (e.g., `172.105.xxx.xxx`).
    *   **TTL**: Leave as Default.
4.  Click **Save**.

## Step 3: Update NameServers at NextHosting

For the Step 2 settings to work, your domain must "ask" Linode for directions.

1.  Log in to your **NextHosting** Client Area.
2.  Navigate to **Domains** > **My Domains**.
3.  Manage `ehub.co.tz` > **Nameservers**.
4.  Select **Use Custom Nameservers** (enter below):
    *   `ns1.linode.com`
    *   `ns2.linode.com`
    *   `ns3.linode.com`
    *   `ns4.linode.com`
    *   `ns5.linode.com`
5.  **Save Changes**.
    *   *Note: Propagation can take 1-24 hours.*

---

## Step 4: Configure the Project (I have done this for you)

I will now update your Django project to accept requests from this new domain.

1.  I am updating `settings.py` to allow `eduka.ehub.co.tz`.
2.  **You need to pull these changes**:
    ```bash
    ssh root@<your-server-ip>
    cd /path/to/eduka_backend
    git pull origin main
    ```

## Step 5: Update Nginx on Server

Final step to tell your web server to listen for this name.

1.  Edit your Nginx config:
    ```bash
    sudo nano /etc/nginx/sites-available/eduka_backend
    ```
2.  Find `server_name` and add/change it:
    ```nginx
    server_name eduka.ehub.co.tz;
    ```
3.  Save and Restart:
    ```bash
    sudo systemctl restart nginx
    sudo systemctl restart gunicorn
    ```

## Step 6: Secure with SSL (HTTPS)

If you get a "command not found" error, you need to install Certbot first:

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

Then run the setup command:
```bash
sudo certbot --nginx -d eduka.ehub.co.tz
```
