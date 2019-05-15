from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Cuisine, Recipe


engine = create_engine('sqlite:///catalogwithdatedb.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create African Cuisine
cuisine1 = Cuisine(name="African Cuisine")
session.add(cuisine1)
session.commit()

af_recipe1 = Recipe(name="East African Braised Chicken",
                    description="""The Indian spice trade carried curry throughout East Africa.
                     Popular curry dishes like this aromatic chicken
                     braised in broth with dates and raisins also combines traditional African braising techniques.""",
                    cuisine=cuisine1)
session.add(af_recipe1)
session.commit()

af_recipe2 = Recipe(name="Red Whole Wheat Penne",
                    description="""According to chef Marcus Samuelsson, "A brief
                    Italian occupation from 1936 to 1941 left a European presence
                    evident in Ethiopia's cathedrals and in dishes like pasta
                    saltata." Here is the chef's modern version of the now-classic
                    Ethiopian dish-minus all the butter and oil.""",
                    cuisine=cuisine1)
session.add(af_recipe2)
session.commit()

af_recipe3 = Recipe(name="African Chicken in Spicy Red Sauce",
                    description="""This flavorful Ethiopian-inspired chicken stew
                    recipe uses Berbere, an Ethiopian spice blend. Store extra
                    spice mix covered in a cool, dark place for up to two weeks.
                    Use leftovers on salmon, flank steak, or chicken for fiery
                    flavor. Serve with basmati rice.""",
                    cuisine=cuisine1)
session.add(af_recipe3)
session.commit()

# Create Asian cuisine
cuisine2 = Cuisine(name="Asian Cuisine")
session.add(cuisine2)
session.commit()

as_recipe1 = Recipe(name="Thai Green Curry with Shrimp and Kale",
                    description="""Lacinato kale ups the green in this green
                    curry dish, providing a delightful textural contrast to
                    the tender rice noodles.""",
                    cuisine=cuisine2)
session.add(as_recipe1)
session.commit()

as_recipe2 = Recipe(name="Chicken Thighs With Ginger-Sesame Glaze",
                    description="""Make-ahead tip: Mix up the glaze first thing
                    in the morning, and allow the chicken thighs to marinate all
                    day long in the refrigerator to soak up even more flavor.
                    After that, getting dinner on the table is as simple as
                    heating up the grill pan.""",
                    cuisine=cuisine2)
session.add(as_recipe2)
session.commit()

as_recipe3 = Recipe(name="Sweet and Sour Chicken",
                    description="""Our take saves 446 calories, 22 grams
                    of fat, and 1,260 milligrams of sodium over one
                    serving of a leading chain's sweet and sour chicken.""",
                    cuisine=cuisine2)
session.add(as_recipe3)
session.commit()

# Create European cuisine
cuisine3 = Cuisine(name="European Cuisine")
session.add(cuisine3)
session.commit()

eu_recipe1 = Recipe(name="Irish Winter Stew Recipe",
                    description="""Juicy cubes of mutton tossed with potatoes
                    and seasoned with carrots, springs onions. It's a rich and
                    hearty Irish feast!""",
                    cuisine=cuisine3)
session.add(eu_recipe1)
session.commit()

# Create Oceanian cuisine
cuisine4 = Cuisine(name="Oceanian Cuisine")
session.add(cuisine4)
session.commit()


print("Complete!")
