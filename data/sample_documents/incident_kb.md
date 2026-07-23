# Incident Knowledge Base

## Common Network Incidents

### Network Timeout
**Symptoms:** Slow response times, connection timeouts
**Root Cause:** Network congestion, firewall blocking, DNS issues
**Resolution:**
1. Check network connectivity: `ping google.com`
2. Check DNS resolution: `nslookup google.com`
3. Check firewall rules: Review iptables/Windows Firewall
4. Check bandwidth usage: Use `nethogs` or Task Manager

### Service Not Responding
**Symptoms:** 503 errors, connection refused
**Root Cause:** Service crashed, port blocked, resource exhaustion
**Resolution:**
1. Check service status: `systemctl status <service>`
2. Check logs: `journalctl -u <service> -n 50`
3. Restart service: `systemctl restart <service>`
4. Check resource usage: `top`, `htop`

### Database Connection Issues
**Symptoms:** Connection refused, slow queries, connection pool exhaustion
**Root Cause:** Database down, network issues, connection pool misconfiguration
**Resolution:**
1. Check database status: `pg_isready` (PostgreSQL) or `mysqladmin ping` (MySQL)
2. Check connection string: Verify host, port, credentials
3. Check connection pool settings: Increase max_connections
4. Check network connectivity: `telnet <db_host> <db_port>`

## Common Application Incidents

### High CPU Usage
**Symptoms:** Slow performance, high load average
**Root Cause:** Inefficient queries, memory leaks, inefficient algorithms
**Resolution:**
1. Identify top CPU processes: `top`, `htop`
2. Profile application: Use cProfile, Py-Spy
3. Optimize queries: Add indexes, rewrite queries
4. Scale horizontally: Add more instances

### Memory Leaks
**Symptoms:** Gradual memory increase, OOM kills
**Root Cause:** Unreleased resources, circular references, inefficient data structures
**Resolution:**
1. Monitor memory usage: `top`, `free -h`
2. Use memory profiler: `memory_profiler`, `tracemalloc`
3. Fix leaks: Release resources, use weak references
4. Implement limits: Set memory limits in deployment config

## Emergency Contacts

- On-call Engineer: +1-555-1234
- DevOps Lead: +1-555-5678
- Manager: +1-555-9012