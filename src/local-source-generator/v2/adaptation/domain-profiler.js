/**
 * Domain Profiler - Tracks domain metrics over time for drift detection
 * 
 * Optional component for tracking changes in domain characteristics
 * between scans to detect significant changes (drift).
 */

import { fs, path } from 'zx';

export class DomainProfiler {
    constructor(options = {}) {
        this.profileDir = options.profileDir || path.join(process.cwd(), 'domain-profiles');
        this.profiles = new Map();
    }

    /**
     * Initialize profiler - ensure directory exists
     */
    async init() {
        await fs.ensureDir(this.profileDir);
        return this;
    }

    /**
     * Update profile for a domain with new metrics
     * @param {string} domain - Domain name
     * @param {object} metrics - Current metrics
     * @returns {Promise<object>} Updated profile
     */
    async updateProfile(domain, metrics) {
        const profilePath = path.join(this.profileDir, `${domain}.json`);
        
        let profile = {
            domain,
            firstSeen: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
            scans: [],
            currentMetrics: metrics,
            drift_score: 0
        };

        // Load existing profile if exists
        try {
            if (await fs.pathExists(profilePath)) {
                const existing = JSON.parse(await fs.readFile(profilePath, 'utf-8'));
                profile.firstSeen = existing.firstSeen || profile.firstSeen;
                profile.scans = existing.scans || [];
            }
        } catch (err) {
            // Start fresh if can't load
        }

        // Add current scan
        profile.scans.push({
            timestamp: new Date().toISOString(),
            metrics: { ...metrics }
        });

        // Keep only last 10 scans
        if (profile.scans.length > 10) {
            profile.scans = profile.scans.slice(-10);
        }

        // Calculate drift score (simple: compare with previous scan)
        if (profile.scans.length > 1) {
            const previous = profile.scans[profile.scans.length - 2].metrics;
            const current = metrics;
            
            // Simple drift calculation: count significant changes
            let changes = 0;
            let total = 0;
            
            for (const key in current) {
                if (previous[key] !== undefined) {
                    total++;
                    const change = Math.abs((current[key] || 0) - (previous[key] || 0));
                    const threshold = previous[key] * 0.2; // 20% change threshold
                    if (change > threshold) {
                        changes++;
                    }
                }
            }
            
            profile.drift_score = total > 0 ? changes / total : 0;
        }

        profile.lastUpdated = new Date().toISOString();
        profile.currentMetrics = metrics;

        // Save profile
        await fs.writeFile(profilePath, JSON.stringify(profile, null, 2));

        this.profiles.set(domain, profile);
        return profile;
    }

    /**
     * Check if domain has drifted significantly
     * @param {string} domain - Domain name
     * @param {number} threshold - Drift threshold (default 0.3 = 30%)
     * @returns {boolean} True if drifted
     */
    hasDrifted(domain, threshold = 0.3) {
        const profile = this.profiles.get(domain);
        if (!profile) {
            return false;
        }
        return profile.drift_score >= threshold;
    }

    /**
     * Get profile for domain
     * @param {string} domain - Domain name
     * @returns {object|null} Profile or null
     */
    getProfile(domain) {
        return this.profiles.get(domain) || null;
    }
}

