/**
 * Priya API Client for Nuxt Frontend
 */

export interface PromotionLink {
  id: number
  original_url: string
  normalized_url: string
  destination_domain: string
  link_type: string
  is_primary: boolean
}

export interface Promotion {
  id: number
  provider_id: number
  provider_slug?: string
  provider_name?: string
  plan_id?: number
  plan_slug?: string
  plan_name?: string
  title: string
  description?: string
  offer_type: string
  discount_percentage?: number
  duration_days?: number
  promo_code?: string
  eligible_countries: string[]
  excluded_countries: string[]
  account_requirements: Record<string, any>
  payment_required?: boolean
  status: 'unverified' | 'likely_valid' | 'verified' | 'expired' | 'restricted' | 'invalid'
  confidence_score: number
  first_discovered_at: string
  last_discovered_at: string
  discoveries_count: number
  links: PromotionLink[]
}

export interface ProviderPlan {
  id: number
  name: string
  slug: string
  description?: string
  is_active: boolean
}

export interface Provider {
  id: number
  name: string
  slug: string
  description?: string
  website_url?: string
  is_active: boolean
  plans_count: number
  promotions_count: number
  plans: ProviderPlan[]
}

export interface ActivityItem {
  id: number
  source_name: string
  source_type: string
  title?: string
  processing_status: string
  discovered_at: string
}

export interface DashboardStats {
  total_discovered_items: number
  total_promotions: number
  verified_promotions: number
  likely_valid_promotions: number
  expiring_promotions: number
  nigeria_eligible_promotions: number
  providers: {
    provider_id: number
    name: string
    slug: string
    promotions_count: number
    verified_count: number
    avg_confidence: number
  }[]
  offer_type_distribution: Record<string, number>
  recent_discoveries: {
    id: number
    provider_name: string
    provider_slug: string
    plan_name?: string
    title: string
    offer_type: string
    status: string
    confidence_score: number
    is_nigeria_eligible: boolean
    first_discovered_at: string
  }[]
}

export interface VerificationCheck {
  id: number
  check_type: string
  result: 'pass' | 'fail' | 'warning'
  status: string
  details: Record<string, any>
  checked_at: string
}

export interface EligibilityRule {
  id: number
  rule_type: string
  country_code?: string
  description: string
  evidence_url?: string
}

export interface PromotionEligibility {
  promotion_id: number
  status: string
  is_nigeria_eligible: boolean
  payment_card_guidance: string
  summary_notes: string
  rules: EligibilityRule[]
}

export interface PromotionVerifyResult {
  promotion_id: number
  confidence_score: number
  status: string
  is_safe: boolean
  summary_reasons: Record<string, string>
  verification_checks: VerificationCheck[]
}

export interface Source {
  id: number
  source_type: string
  name: string
  identifier: string
  is_active: boolean
  last_polled_at?: string
  discovered_items_count: number
}

export interface WatchlistSummary {
  promotion_ids: number[]
  provider_ids: number[]
  total_saved_promotions: number
  total_watched_providers: number
}

export interface UserPreferences {
  min_confidence_score: number
  nigeria_only_filter: boolean
  telegram_notifications_enabled: boolean
  polling_interval_minutes: number
  auto_verify_links: boolean
  theme: string
}

export class PriyaApiClient {
  private baseUrl: string

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || 'http://localhost:8000/api/v1'
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    })

    if (!res.ok) {
      let detail = `API request failed with status ${res.status}`
      try {
        const errorData = await res.json()
        if (errorData.detail) detail = errorData.detail
      } catch {}
      throw new Error(detail)
    }

    return res.json() as Promise<T>
  }

  getHealth() {
    return this.request<{ status: string; app: string; database: { status: string; latency_ms: number } }>('/health')
  }

  getDashboardStats() {
    return this.request<DashboardStats>('/dashboard/stats')
  }

  getDashboardActivity(limit: number = 20) {
    return this.request<ActivityItem[]>(`/dashboard/activity?limit=${limit}`)
  }

  getPromotions(params: {
    provider_id?: number
    status?: string
    offer_type?: string
    min_confidence?: number
    nigeria_eligible?: boolean
    limit?: number
  } = {}) {
    const query = new URLSearchParams()
    if (params.provider_id) query.set('provider_id', String(params.provider_id))
    if (params.status) query.set('status', params.status)
    if (params.offer_type) query.set('offer_type', params.offer_type)
    if (params.min_confidence !== undefined) query.set('min_confidence', String(params.min_confidence))
    if (params.nigeria_eligible !== undefined) query.set('nigeria_eligible', String(params.nigeria_eligible))
    if (params.limit) query.set('limit', String(params.limit))

    const qs = query.toString()
    return this.request<Promotion[]>(`/promotions${qs ? '?' + qs : ''}`)
  }

  getPromotion(id: number) {
    return this.request<Promotion>(`/promotions/${id}`)
  }

  verifyPromotion(id: number, networkCheck: boolean = false) {
    return this.request<PromotionVerifyResult>(`/promotions/${id}/verify?perform_network_check=${networkCheck}`, {
      method: 'POST'
    })
  }

  getPromotionEligibility(id: number) {
    return this.request<PromotionEligibility>(`/promotions/${id}/eligibility`)
  }

  getPromotionChecks(id: number) {
    return this.request<VerificationCheck[]>(`/promotions/${id}/verification-checks`)
  }

  getProviders() {
    return this.request<Provider[]>('/providers')
  }

  getSources() {
    return this.request<Source[]>('/sources')
  }

  collectSource(sourceId: number) {
    return this.request<{ source_id: number; items_discovered: number }>(`/sources/${sourceId}/collect`, {
      method: 'POST'
    })
  }

  collectAll() {
    return this.request<{ total_items_discovered: number }>('/discovery/collect-all', {
      method: 'POST'
    })
  }

  runProcessing(limit: number = 50) {
    return this.request<{ items_processed: number; promotions_created: number; promotions_corroborated: number }>(
      `/processing/run?limit=${limit}`,
      { method: 'POST' }
    )
  }

  getWatchlist() {
    return this.request<WatchlistSummary>('/watchlist')
  }

  togglePromotionWatchlist(promotionId: number) {
    return this.request<WatchlistSummary>(`/watchlist/promotions/${promotionId}`, { method: 'POST' })
  }

  getWatchlistItems() {
    return this.request<Promotion[]>('/watchlist/items')
  }

  toggleProviderWatchlist(providerId: number) {
    return this.request<WatchlistSummary>(`/watchlist/providers/${providerId}`, { method: 'POST' })
  }

  getSettings() {
    return this.request<UserPreferences>('/settings')
  }

  updateSettings(data: Partial<UserPreferences>) {
    return this.request<UserPreferences>('/settings', {
      method: 'PATCH',
      body: JSON.stringify(data)
    })
  }

  sendTestNotification(customMessage?: string) {
    return this.request<{ success: boolean; is_configured: boolean; detail: string }>(
      '/notifications/test',
      {
        method: 'POST',
        body: JSON.stringify({ custom_message: customMessage })
      }
    )
  }

  getNotifications(limit: number = 20) {
    return this.request<any[]>(`/notifications?limit=${limit}`)
  }
}

export const priyaApi = new PriyaApiClient()
