"""Day 1 customer API analysis project."""
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt
import pandas as pd
import requests

API_URL = "https://jsonplaceholder.typicode.com/users"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def get_customers(url: str = API_URL) -> list[dict]:
    """Fetch customers and report network or response errors clearly."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        customers = response.json()
        if not isinstance(customers, list) or not all(isinstance(row, dict) for row in customers):
            raise ValueError("Expected a JSON list of customer objects")
        return customers
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError(f"Could not retrieve valid customer data from {url}: {exc}") from exc


def explore(record: dict, indent: int = 0) -> None:
    """Print each key and value type, including nested dictionaries."""
    for key, value in record.items():
        print(f"{'  ' * indent}{key}: {type(value).__name__}")
        if isinstance(value, dict):
            explore(value, indent + 1)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    explore(item, indent + 1)


def _domain(email: str) -> str:
    host = email.rsplit("@", 1)[-1]
    return host.rsplit(".", 1)[-1].lower() if "@" in email and "." in host else ""


def _as_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def extract_attributes(customers: list[dict]) -> list[dict]:
    """Flatten customers to the attributes required by the output CSV."""
    rows = []
    for customer in customers:
        address = customer.get("address") or {}
        geo = address.get("geo") or {}
        email = str(customer.get("email", ""))
        rows.append({
            "customer_id": customer.get("id"), "name": customer.get("name", ""),
            "username": customer.get("username", ""), "email": email,
            "email_domain": _domain(email), "phone": customer.get("phone", ""),
            "city": address.get("city", ""), "zipcode": address.get("zipcode", ""),
            "latitude": _as_float(geo.get("lat")), "longitude": _as_float(geo.get("lng")),
            "company": (customer.get("company") or {}).get("name", ""),
            "website": customer.get("website", ""),
        })
    return rows


def unique_cities(customers: list[dict]) -> set[str]:
    return {str((customer.get("address") or {}).get("city", "")) for customer in customers}


def city_counts(customers: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for customer in customers:
        city = str((customer.get("address") or {}).get("city", ""))
        counts[city] = counts.get(city, 0) + 1
    return counts


def email_domain_counts(customers: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for customer in customers:
        domain = _domain(str(customer.get("email", "")))
        counts[domain] = counts.get(domain, 0) + 1
    return dict(sorted(counts.items()))


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    columns = ["customer_id", "name", "username", "email", "email_domain", "phone", "city", "zipcode", "latitude", "longitude", "company", "website"]
    return pd.DataFrame(rows, columns=columns)


def plot_distribution(counts: dict[str, int], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
    cities, values = [pair[0] for pair in ordered], [pair[1] for pair in ordered]
    fig, ax = plt.subplots(figsize=(max(8, len(cities) * 0.8), 5))
    ax.bar(cities, values, color="#2563eb")
    ax.set(title="Customer Distribution by City", xlabel="City", ylabel="Customer Count")
    ax.tick_params(axis="x", labelrotation=35)
    for label in ax.get_xticklabels():
        label.set_horizontalalignment("right")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    customers = get_customers()
    rows = extract_attributes(customers)
    to_dataframe(rows).to_csv(OUTPUT_DIR / "customers.csv", index=False)
    city_rows = sorted(city_counts(customers).items(), key=lambda pair: (-pair[1], pair[0]))
    pd.DataFrame(city_rows, columns=["city", "customer_count"]).to_csv(OUTPUT_DIR / "city_counts.csv", index=False)
    chart_path = OUTPUT_DIR / "customer_distribution.png"
    plot_distribution(dict(city_rows), chart_path)
    city, count = city_rows[0] if city_rows else ("N/A", 0)
    print(f"Customers retrieved : {len(customers)}")
    print(f"Unique cities       : {len(unique_cities(customers))}")
    print(f"Most common city    : {city} ({count})")
    print(f"Email domains       : {email_domain_counts(customers)}")
    print(f"Chart saved to      : output/{chart_path.name}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc))


def run_eda(df: pd.DataFrame) -> None:
    print("\n--- EDA: dataset shape ---")
    print(df.shape)

    print("\n--- EDA: column types and non-null values ---")
    df.info()

    print("\n--- EDA: numerical summary ---")
    print(df.describe())

    print("\n--- EDA: customers by city ---")
    print(df["city"].value_counts())

    print("\n--- EDA: email domains ---")
    print(df["email_domain"].value_counts())
        
