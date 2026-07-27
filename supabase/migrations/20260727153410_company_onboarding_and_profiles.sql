create table if not exists public.company_profiles (
	id uuid primary key references auth.users (id) on delete cascade,
	company_name text not null,
	company_email text not null unique,
	subscription_tier text not null check (subscription_tier in ('starter', 'scale', 'enterprise')),
	onboarding_completed boolean not null default false,
	created_at timestamptz not null default timezone('utc', now()),
	updated_at timestamptz not null default timezone('utc', now())
);

create index if not exists idx_company_profiles_company_email on public.company_profiles (company_email);

create or replace function public.set_company_profiles_updated_at()
returns trigger
language plpgsql
as $$
begin
	new.updated_at = timezone('utc', now());
	return new;
end;
$$;

drop trigger if exists trg_company_profiles_updated_at on public.company_profiles;
create trigger trg_company_profiles_updated_at
before update on public.company_profiles
for each row
execute procedure public.set_company_profiles_updated_at();

alter table public.company_profiles enable row level security;

drop policy if exists "Users can view own company profile" on public.company_profiles;
create policy "Users can view own company profile"
on public.company_profiles
for select
to authenticated
using (auth.uid() = id);

drop policy if exists "Users can insert own company profile" on public.company_profiles;
create policy "Users can insert own company profile"
on public.company_profiles
for insert
to authenticated
with check (auth.uid() = id);

drop policy if exists "Users can update own company profile" on public.company_profiles;
create policy "Users can update own company profile"
on public.company_profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);
