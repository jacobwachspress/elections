import geo_helper.helper_tools.shp_manipulation as sm
import geo_helper.helper_tools.file_management as fm


def dissolve_by_attribute(in_path, dissolve_attribute, out_path=False):
	'''Remove boundaries according to attribute.

	Dissolve boundaries for shapefile(s) according to a given attribute. We
	will also check for contiguity after boundaries have been dissolved.

	Arguments:
		in_path:
			full path to input shapefile to be dissolved

		out_path:
			full path to save created shapefile

		disolve_attribute:
			attribute to dissolve boundaries by
	'''
	#  Generate dissolved shapefile
	df = fm.load_shapefile(in_path)
	df = sm.dissolve(df, dissolve_attribute)

	# Save shapefile
	if out_path:
		fm.save_shapefile(df, out_path)

	return df
